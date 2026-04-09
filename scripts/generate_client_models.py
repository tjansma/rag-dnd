import argparse
import json
from pathlib import Path
import tempfile

parser = argparse.ArgumentParser()
parser.add_argument("output", type=str, help="Output file")
args = parser.parse_args()

from datamodel_code_generator import generate, DataModelType, InputFileType

from rag_dnd.server import app

oas_spec = app.openapi()
generate(oas_spec,
         input_file_type=InputFileType.OpenAPI,
         output_model_type=DataModelType.PydanticV2BaseModel,
         output=Path(args.output))

print(f"OpenAPI spec saved to {args.output}")
