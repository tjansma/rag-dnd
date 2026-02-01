"""Module for handling LLMs."""
import logging

from transformers import AutoModelForCausalLM, AutoTokenizer

SUPPORTED_MODELS = [ "Qwen/Qwen3-4B-Instruct-2507-FP8" ]
SUPPORTED_DEVICES = [ "cpu", "cuda", "auto" ]

logger = logging.getLogger(__name__)

llm_instances = {}

class HuggingFaceLLM:
    """HuggingFaceLLM for generating responses."""
    def __init__(self, model_name: str, device: str = "auto") -> None:
        """
        Initialize the HuggingFaceLLM.
        
        Args:
            model_name (str): The name of the model to use.
            device (str): The device to use.
            
        Returns:
            None
        """
        logger.debug(f"Initializing HuggingFaceLLM with model: {model_name} on device: {device}")
        if model_name not in SUPPORTED_MODELS:
            logger.error(f"Model {model_name} is not supported. Supported models: {SUPPORTED_MODELS}")
            raise ValueError(f"Model {model_name} is not supported. Supported models: {SUPPORTED_MODELS}")
        
        if device not in SUPPORTED_DEVICES:
            logger.error(f"Device {device} is not supported. Supported devices: {SUPPORTED_DEVICES}")
            raise ValueError(f"Device {device} is not supported. Supported devices: {SUPPORTED_DEVICES}")
        
        self.model_name = model_name
        self.device = device
        
        logger.debug(f"Loading tokenizer for model: {model_name}")
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        
        logger.debug(f"Loading model for model: {model_name}")
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_name,
            dtype="auto",
            device_map=self.device)
        
        self.running_on_device = next(self.model.parameters()).device
        logger.info(f"Initialized HuggingFaceLLM with model: {self.model_name} on device: {self.running_on_device}")

    def generate(self, prompt: str) -> str:
        """
        Generate a response from the model.
        
        Args:
            prompt (str): The prompt to generate a response from.
            
        Returns:
            str: The generated response.
        """
        logger.debug(f"Generating response for prompt: {prompt} using model: {self.model_name} on device: {self.device} with tokenizer: {self.tokenizer}")

        logger.debug(f"Tokenizing prompt: {prompt}")
        inputs = self.tokenizer([prompt], return_tensors="pt").to(self.model.device)
        logger.debug(f"Generating response")
        generated_ids = self.model.generate(**inputs, max_new_tokens=512)
        output_ids = generated_ids[0][len(inputs.input_ids[0]):].tolist()
        logger.debug(f"Decoding response")
        response = self.tokenizer.decode(output_ids, skip_special_tokens=True)
        logger.debug(f"Generated response: {response}")
        return response

def get_llm(model_name: str, device: str = "auto") -> HuggingFaceLLM:
    """
    Get a HuggingFaceLLM instance for the given model name.
    
    Args:
        model_name (str): The name of the model to use.
        device (str): The device to use.
        
    Returns:
        HuggingFaceLLM: The HuggingFaceLLM instance.
    """
    global llm_instances
    logger.debug(f"Getting HuggingFaceLLM instance for model: {model_name}")
    if model_name in llm_instances and llm_instances[model_name].device == device:
        logger.debug(f"Using existing HuggingFaceLLM instance for model: {model_name} on device: {device}")
        return llm_instances[model_name]
    else:
        logger.debug(f"Creating new HuggingFaceLLM instance for model: {model_name} on device: {device}")
        llm = HuggingFaceLLM(model_name, device)
        llm_instances[model_name] = llm
        return llm

def unload_llm(model_name: str) -> None:
    """
    Unload a HuggingFaceLLM instance for the given model name.
    
    Args:
        model_name (str): The name of the model to unload.
        
    Returns:
        None
    """
    global llm_instances
    logger.debug(f"Unloading HuggingFaceLLM instance for model: {model_name}")
    if model_name in llm_instances:
        logger.debug(f"Unloading HuggingFaceLLM instance for model: {model_name}")
        del llm_instances[model_name]
    else:
        logger.debug(f"No HuggingFaceLLM instance found for model: {model_name}")
