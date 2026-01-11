import re
import datetime

log_file = r"c:\Development\src\_AI\rag_dnd\log\rag_dnd.log"

# Regex patterns
time_pattern = re.compile(r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3})")
chunk_start_pattern = re.compile(r"Embedding chunk: (\d+).*Sentences count: (\d+)")
chunk_start_simple_pattern = re.compile(r"Embedding chunk: (\d+)") # For fallback if count is on next line or missing
chunk_end_pattern = re.compile(r"Adding chunk to vector store: (\d+)")

data = {} # chunk_id -> {start, sentences}
results = []

with open(log_file, "r") as f:
    # Read entire file to handle multi-line or split log messages if needed, 
    # but single line processing is usually safer for simple logs unless wrapped.
    # The previous grep showed "Sentences count" on the SAME LINE as "Embedding chunk" usually.
    # But grep output can be misleading. Let's assume same line for now based on the successful grep hits.
    
    for line in f:
        match = time_pattern.match(line)
        if not match:
            continue
        
        timestamp_str = match.group(1)
        timestamp = datetime.datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S,%f")

        # Try to find start + count
        start_match = chunk_start_pattern.search(line)
        if start_match:
            chunk_id = int(start_match.group(1))
            count = int(start_match.group(2))
            data[chunk_id] = {"start": timestamp, "count": count}
        else:
            # Fallback for start without count on same line (maybe log message was split or formatted differently)
            simple_start = chunk_start_simple_pattern.search(line)
            if simple_start:
                chunk_id = int(simple_start.group(1))
                if chunk_id not in data:
                    data[chunk_id] = {"start": timestamp, "count": 0} # 0 indicates unknown

        # Check for end
        end_match = chunk_end_pattern.search(line)
        if end_match:
            chunk_id = int(end_match.group(1))
            if chunk_id in data:
                start_time = data[chunk_id]["start"]
                count = data[chunk_id]["count"]
                duration = (timestamp - start_time).total_seconds()
                results.append({
                    "id": chunk_id,
                    "start": start_time,
                    "duration": duration,
                    "count": count,
                    "rate": count / duration if duration > 0 else 0
                })
                del data[chunk_id]

# Sort by start time
results.sort(key=lambda x: x["start"])

print(f"{'Chunk':<6} {'Start Time':<24} {'Dur(s)':<8} {'Count':<6} {'Rate(s/s)':<10}")
print("-" * 65)

for r in results[-50:]:
    print(f"{r['id']:<6} {r['start'].strftime('%H:%M:%S.%f'):<24} {r['duration']:<8.3f} {r['count']:<6} {r['rate']:<10.1f}")
