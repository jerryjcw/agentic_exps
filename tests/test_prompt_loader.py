"""
Unit tests for the YAML prompt configuration and loader.
"""

import unittest
import os
import sys
from pathlib import Path

# Add the project root to the path so we can import modules
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from agent_optimizer.config_loader import OptimizerConfigLoader, get_optimizer_config
from agent_optimizer.types import OptimizationObjective


class TestOptimizerConfigLoader(unittest.TestCase):
    """Test cases for the OptimizerConfigLoader class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.loader = get_optimizer_config()
    
    def test_critic_prompts(self):
        """Test loading critic prompts."""
        # Test main evaluation prompt
        main_eval = self.loader.get_critic_prompt('main_evaluation')
        self.assertIsInstance(main_eval, str)
        self.assertGreater(len(main_eval), 100)
        self.assertIn('expected', main_eval.lower())
        self.assertIn('actual', main_eval.lower())
        
        # Test specific objective prompts
        accuracy_prompt = self.loader.get_critic_prompt('accuracy')
        self.assertIsInstance(accuracy_prompt, str)
        self.assertGreater(len(accuracy_prompt), 100)
        self.assertIn('accuracy', accuracy_prompt.lower())
        
        fluency_prompt = self.loader.get_critic_prompt('fluency')
        self.assertIsInstance(fluency_prompt, str)
        self.assertIn('fluency', fluency_prompt.lower())
        
        factuality_prompt = self.loader.get_critic_prompt('factuality')
        self.assertIsInstance(factuality_prompt, str)
        self.assertIn('factual', factuality_prompt.lower())
        
        instruction_prompt = self.loader.get_critic_prompt('instruction_following')
        self.assertIsInstance(instruction_prompt, str)
        self.assertIn('instruction', instruction_prompt.lower())
    
    def test_critic_system_messages(self):
        """Test loading critic system messages."""
        system_msg = self.loader.get_critic_system_message('default')
        self.assertIsInstance(system_msg, str)
        self.assertGreater(len(system_msg), 10)
        self.assertIn('evaluator', system_msg.lower())
    
    def test_suggester_prompts(self):
        """Test loading suggester prompts."""
        accuracy_suggestion = self.loader.get_suggester_prompt('accuracy')
        self.assertIsInstance(accuracy_suggestion, str)
        self.assertGreater(len(accuracy_suggestion), 100)
        self.assertIn('accuracy', accuracy_suggestion.lower())
        self.assertIn('prompt engineer', accuracy_suggestion.lower())
        
        fluency_suggestion = self.loader.get_suggester_prompt('fluency')
        self.assertIsInstance(fluency_suggestion, str)
        self.assertIn('fluency', fluency_suggestion.lower())
        
        factuality_suggestion = self.loader.get_suggester_prompt('factuality')
        self.assertIsInstance(factuality_suggestion, str)
        self.assertIn('factual', factuality_suggestion.lower())
        
        instruction_suggestion = self.loader.get_suggester_prompt('instruction_following')
        self.assertIsInstance(instruction_suggestion, str)
        self.assertIn('instruction', instruction_suggestion.lower())
    
    def test_suggester_system_messages(self):
        """Test loading suggester system messages."""
        system_msg = self.loader.get_suggester_system_message('default')
        self.assertIsInstance(system_msg, str)
        self.assertGreater(len(system_msg), 50)
        self.assertIn('prompt engineer', system_msg.lower())
        self.assertIn('json', system_msg.lower())
    
    def test_improvement_additions(self):
        """Test loading improvement additions."""
        accuracy_additions = self.loader.get_improvement_additions('accuracy_additions')
        self.assertIsInstance(accuracy_additions, list)
        self.assertGreater(len(accuracy_additions), 0)
        self.assertTrue(all(isinstance(item, str) for item in accuracy_additions))
        
        detail_additions = self.loader.get_improvement_additions('detail_additions')
        self.assertIsInstance(detail_additions, list)
        self.assertGreater(len(detail_additions), 0)
        
        format_additions = self.loader.get_improvement_additions('format_additions')
        self.assertIsInstance(format_additions, list)
        self.assertGreater(len(format_additions), 0)
        
        context_additions = self.loader.get_improvement_additions('context_additions')
        self.assertIsInstance(context_additions, list)
        self.assertGreater(len(context_additions), 0)
    
    def test_improvement_templates(self):
        """Test loading improvement templates."""
        error_handling = self.loader.get_improvement_template('error_handling')
        self.assertIsInstance(error_handling, str)
        self.assertGreater(len(error_handling), 20)
        self.assertIn('error', error_handling.lower())
        
        output_length = self.loader.get_improvement_template('output_length')
        self.assertIsInstance(output_length, str)
        self.assertGreater(len(output_length), 20)
        self.assertIn('output', output_length.lower())
    
    def test_templates(self):
        """Test loading common templates."""
        json_format = self.loader.get_template('json_response_format')
        self.assertIsInstance(json_format, str)
        self.assertIn('score', json_format)
        self.assertIn('feedback', json_format)
        
        suggestion_format = self.loader.get_template('suggestion_format')
        self.assertIsInstance(suggestion_format, str)
        self.assertIn('agent_id', suggestion_format)
        self.assertIn('new_prompt', suggestion_format)
    
    def test_common_instructions(self):
        """Test loading common instructions."""
        eval_guidelines = self.loader.get_common_instructions('evaluation_guidelines')
        self.assertIsInstance(eval_guidelines, str)
        self.assertGreater(len(eval_guidelines), 50)
        self.assertIn('score', eval_guidelines.lower())
        
        suggestion_guidelines = self.loader.get_common_instructions('suggestion_guidelines')
        self.assertIsInstance(suggestion_guidelines, str)
        self.assertGreater(len(suggestion_guidelines), 50)
        self.assertIn('improvement', suggestion_guidelines.lower())
    
    def test_get_all_prompts(self):
        """Test getting all prompts at once."""
        all_critic = self.loader.get_all_critic_prompts()
        self.assertIsInstance(all_critic, dict)
        self.assertIn('accuracy', all_critic)
        self.assertIn('fluency', all_critic)
        self.assertIn('factuality', all_critic)
        self.assertIn('instruction_following', all_critic)
        
        all_suggester = self.loader.get_all_suggester_prompts()
        self.assertIsInstance(all_suggester, dict)
        self.assertIn('accuracy', all_suggester)
        self.assertIn('fluency', all_suggester)
        self.assertIn('factuality', all_suggester)
        self.assertIn('instruction_following', all_suggester)
    
    def test_raw_config(self):
        """Test getting raw configuration."""
        raw_config = self.loader.get_raw_config()
        self.assertIsInstance(raw_config, dict)
        self.assertIn('critic', raw_config)
        self.assertIn('suggester', raw_config)
        self.assertIn('templates', raw_config)


class TestComponentIntegration(unittest.TestCase):
    """Test cases for component integration with YAML configuration."""
    
    def test_critic_initialization(self):
        """Test that OutputEvaluator initializes correctly with YAML config."""
        from agent_optimizer.critic import OutputEvaluator
        
        critic = OutputEvaluator()
        self.assertIsNotNone(critic.config)
        self.assertIsInstance(critic.evaluation_prompts, dict)
        self.assertEqual(len(critic.evaluation_prompts), 4)
        
        # Verify all optimization objectives are covered
        self.assertIn(OptimizationObjective.ACCURACY, critic.evaluation_prompts)
        self.assertIn(OptimizationObjective.FLUENCY, critic.evaluation_prompts)
        self.assertIn(OptimizationObjective.FACTUALITY, critic.evaluation_prompts)
        self.assertIn(OptimizationObjective.INSTRUCTION_FOLLOWING, critic.evaluation_prompts)
        
        # Verify prompts are actually loaded
        for objective, prompt in critic.evaluation_prompts.items():
            self.assertIsInstance(prompt, str)
            self.assertGreater(len(prompt), 50)
    
    def test_suggester_initialization(self):
        """Test that SuggestionGenerator initializes correctly with YAML config."""
        from agent_optimizer.suggester import SuggestionGenerator
        
        suggester = SuggestionGenerator()
        self.assertIsNotNone(suggester.config)
        self.assertIsInstance(suggester.suggestion_prompts, dict)
        self.assertEqual(len(suggester.suggestion_prompts), 4)
        
        # Verify all optimization objectives are covered
        self.assertIn(OptimizationObjective.ACCURACY, suggester.suggestion_prompts)
        self.assertIn(OptimizationObjective.FLUENCY, suggester.suggestion_prompts)
        self.assertIn(OptimizationObjective.FACTUALITY, suggester.suggestion_prompts)
        self.assertIn(OptimizationObjective.INSTRUCTION_FOLLOWING, suggester.suggestion_prompts)
        
        # Verify prompts are actually loaded
        for objective, prompt in suggester.suggestion_prompts.items():
            self.assertIsInstance(prompt, str)
            self.assertGreater(len(prompt), 50)
    
    def test_prompt_consistency(self):
        """Test that prompts loaded by components match config loader directly."""
        from agent_optimizer.critic import OutputEvaluator
        from agent_optimizer.suggester import SuggestionGenerator
        
        loader = get_optimizer_config()
        critic = OutputEvaluator()
        suggester = SuggestionGenerator()
        
        # Test critic prompt consistency
        direct_accuracy = loader.get_critic_prompt('accuracy')
        critic_accuracy = critic.evaluation_prompts[OptimizationObjective.ACCURACY]
        self.assertEqual(direct_accuracy, critic_accuracy)
        
        # Test suggester prompt consistency  
        direct_suggestion = loader.get_suggester_prompt('fluency')
        suggester_fluency = suggester.suggestion_prompts[OptimizationObjective.FLUENCY]
        self.assertEqual(direct_suggestion, suggester_fluency)


if __name__ == '__main__':
    unittest.main()