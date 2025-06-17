"""
Prompt management utilities for loading and processing prompts.

Provides:
- Prompt file loading with error handling
- Template substitution
- Prompt validation
"""

from pathlib import Path
from typing import Dict, Any, Optional, List
import re


class PromptManager:
    """Manager for loading and processing prompt templates"""
    
    def __init__(self, prompt_dir: Path, subdirectory: str = ""):
        """
        Initialize prompt manager
        
        Args:
            prompt_dir: Base directory for prompt files
            subdirectory: Optional subdirectory within prompt_dir
        """
        self.prompt_dir = prompt_dir
        self.subdirectory = subdirectory
        self.loaded_prompts: Dict[str, str] = {}
    
    def get_prompt_path(self, filename: str) -> Path:
        """Get full path to prompt file"""
        if self.subdirectory:
            return self.prompt_dir / self.subdirectory / filename
        return self.prompt_dir / filename
    
    def load_prompt(self, filename: str, cache: bool = True) -> str:
        """
        Load prompt from file with error handling
        
        Args:
            filename: Name of the prompt file
            cache: Whether to cache the loaded prompt
            
        Returns:
            Prompt text or empty string if file not found
        """
        if cache and filename in self.loaded_prompts:
            return self.loaded_prompts[filename]
        
        prompt_path = self.get_prompt_path(filename)
        try:
            with open(prompt_path, 'r', encoding='utf-8') as f:
                prompt_text = f.read().strip()
                
            if cache:
                self.loaded_prompts[filename] = prompt_text
                
            return prompt_text
            
        except FileNotFoundError:
            print(f"Warning: Prompt file {prompt_path} not found, using empty prompt")
            return ""
        except Exception as e:
            print(f"Error loading prompt {prompt_path}: {e}")
            return ""
    
    def substitute_template(self, template: str, substitutions: Dict[str, str]) -> str:
        """
        Substitute template variables in prompt
        
        Args:
            template: Template string with {{variable}} placeholders
            substitutions: Dictionary of variable->value mappings
            
        Returns:
            Template with substitutions applied
        """
        result = template
        for variable, value in substitutions.items():
            placeholder = f"{{{{{variable}}}}}"
            result = result.replace(placeholder, str(value))
        return result
    
    def extract_template_variables(self, template: str) -> List[str]:
        """
        Extract template variable names from prompt template
        
        Args:
            template: Template string with {{variable}} placeholders
            
        Returns:
            List of variable names found in template
        """
        pattern = r'\{\{(\w+)\}\}'
        return re.findall(pattern, template)
    
    def validate_template(self, template: str, required_vars: List[str]) -> bool:
        """
        Validate that template contains all required variables
        
        Args:
            template: Template string to validate
            required_vars: List of required variable names
            
        Returns:
            True if all required variables are present
        """
        found_vars = set(self.extract_template_variables(template))
        required_vars_set = set(required_vars)
        return required_vars_set.issubset(found_vars)
    
    def build_prompt(self, filename: str, substitutions: Dict[str, str], 
                    validate_vars: Optional[List[str]] = None) -> str:
        """
        Load prompt template and apply substitutions
        
        Args:
            filename: Name of the prompt file
            substitutions: Dictionary of variable->value mappings
            validate_vars: Optional list of required variables to validate
            
        Returns:
            Processed prompt with substitutions applied
        """
        template = self.load_prompt(filename)
        
        if validate_vars:
            if not self.validate_template(template, validate_vars):
                missing_vars = set(validate_vars) - set(self.extract_template_variables(template))
                print(f"Warning: Template missing required variables: {missing_vars}")
        
        return self.substitute_template(template, substitutions)


# Convenience functions for common use cases
def load_prompt(filename: str, prompt_dir: Path, subdirectory: str = "") -> str:
    """
    Load a single prompt file
    
    Args:
        filename: Name of the prompt file
        prompt_dir: Base directory for prompt files
        subdirectory: Optional subdirectory
        
    Returns:
        Prompt text
    """
    manager = PromptManager(prompt_dir, subdirectory)
    return manager.load_prompt(filename)


def build_prompt_with_substitutions(filename: str, prompt_dir: Path, 
                                   substitutions: Dict[str, str],
                                   subdirectory: str = "") -> str:
    """
    Load prompt and apply substitutions in one step
    
    Args:
        filename: Name of the prompt file
        prompt_dir: Base directory for prompt files
        substitutions: Dictionary of variable->value mappings
        subdirectory: Optional subdirectory
        
    Returns:
        Processed prompt with substitutions applied
    """
    manager = PromptManager(prompt_dir, subdirectory)
    return manager.build_prompt(filename, substitutions) 