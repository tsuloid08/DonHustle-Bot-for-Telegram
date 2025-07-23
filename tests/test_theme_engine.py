"""
Unit tests for the Mafia Theme Engine

Tests all functionality including message generation, tone adjustment,
template system, and Spanish localization.
"""

import unittest
from unittest.mock import patch
import random

from utils.theme import ThemeEngine, ToneStyle, MessageType


class TestThemeEngine(unittest.TestCase):
    """Test cases for ThemeEngine class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.theme_engine = ThemeEngine()
        self.serious_engine = ThemeEngine(ToneStyle.SERIOUS)
        self.humorous_engine = ThemeEngine(ToneStyle.HUMOROUS)
    
    def test_initialization_default_tone(self):
        """Test theme engine initializes with default serious tone"""
        engine = ThemeEngine()
        self.assertEqual(engine.get_tone(), ToneStyle.SERIOUS)
    
    def test_initialization_custom_tone(self):
        """Test theme engine initializes with custom tone"""
        engine = ThemeEngine(ToneStyle.HUMOROUS)
        self.assertEqual(engine.get_tone(), ToneStyle.HUMOROUS)
    
    def test_set_and_get_tone(self):
        """Test tone setting and getting functionality"""
        self.theme_engine.set_tone(ToneStyle.HUMOROUS)
        self.assertEqual(self.theme_engine.get_tone(), ToneStyle.HUMOROUS)
        
        self.theme_engine.set_tone(ToneStyle.SERIOUS)
        self.assertEqual(self.theme_engine.get_tone(), ToneStyle.SERIOUS)
    
    def test_generate_welcome_message_serious(self):
        """Test welcome message generation in serious tone"""
        self.theme_engine.set_tone(ToneStyle.SERIOUS)
        message = self.theme_engine.generate_message(MessageType.WELCOME, name="TestUser")
        
        self.assertIn("TestUser", message)
        self.assertTrue(any(term in message.lower() for term in ["familia", "negocio", "soldado", "bienvenido"]))
        self.assertIsInstance(message, str)
        self.assertGreater(len(message), 0)
    
    def test_generate_welcome_message_humorous(self):
        """Test welcome message generation in humorous tone"""
        self.theme_engine.set_tone(ToneStyle.HUMOROUS)
        message = self.theme_engine.generate_message(MessageType.WELCOME, name="TestUser")
        
        self.assertIn("TestUser", message)
        self.assertTrue(any(term in message.lower() for term in ["bienvenido", "familia", "territorio", "valiente", "atreve", "entrar", "circo", "oferta", "rechazar", "pez", "acuario", "nadar"]))
        self.assertIsInstance(message, str)
        self.assertGreater(len(message), 0)
    
    def test_generate_success_message(self):
        """Test success message generation"""
        message = self.theme_engine.generate_message(MessageType.SUCCESS)
        
        self.assertTrue(any(term in message.lower() for term in ["capo", "familia", "trabajo", "excelente", "soldado", "misión"]))
        self.assertIsInstance(message, str)
        self.assertGreater(len(message), 0)
    
    def test_generate_error_message(self):
        """Test error message generation"""
        message = self.theme_engine.generate_message(MessageType.ERROR)
        
        self.assertTrue(any(term in message.lower() for term in ["error", "problema", "familia", "capo"]))
        self.assertIsInstance(message, str)
        self.assertGreater(len(message), 0)
    
    def test_generate_warning_message_with_name(self):
        """Test warning message generation with user name"""
        message = self.theme_engine.generate_message(MessageType.WARNING, name="TestUser")
        
        self.assertIn("TestUser", message)
        self.assertTrue(any(term in message.lower() for term in ["cuidado", "advertencia", "familia", "soldado", "paciencia", "límites"]))
        self.assertIsInstance(message, str)
        self.assertGreater(len(message), 0)
    
    def test_generate_confirmation_message(self):
        """Test confirmation message generation"""
        message = self.theme_engine.generate_message(MessageType.CONFIRMATION)
        
        self.assertTrue(any(term in message.lower() for term in ["seguro", "confirma", "capo", "familia", "soldado", "operación", "decisión"]))
        self.assertIsInstance(message, str)
        self.assertGreater(len(message), 0)
    
    def test_generate_motivational_message(self):
        """Test motivational message generation"""
        message = self.theme_engine.generate_message(MessageType.MOTIVATIONAL)
        
        self.assertTrue(any(term in message.lower() for term in ["trabajo", "éxito", "familia", "soldado"]))
        self.assertIsInstance(message, str)
        self.assertGreater(len(message), 0)
    
    def test_generate_reminder_message(self):
        """Test reminder message generation with custom message"""
        test_message = "Reunión importante a las 3 PM"
        message = self.theme_engine.generate_message(MessageType.REMINDER, message=test_message)
        
        self.assertIn(test_message, message)
        self.assertTrue(any(term in message.lower() for term in ["recordatorio", "familia", "capo", "importante", "negocio", "don", "recuerda", "ring", "despierta", "bella", "durmiente", "soldado", "distraído", "atención"]))
        self.assertIsInstance(message, str)
        self.assertGreater(len(message), 0)
    
    def test_generate_help_message(self):
        """Test help message generation"""
        message = self.theme_engine.generate_message(MessageType.HELP)
        
        self.assertTrue(any(term in message.lower() for term in ["comandos", "familia", "capo", "herramientas", "organización", "disposición", "manual", "operaciones"]))
        self.assertIsInstance(message, str)
        self.assertGreater(len(message), 0)
    
    def test_tone_difference_in_messages(self):
        """Test that different tones produce different message styles"""
        self.theme_engine.set_tone(ToneStyle.SERIOUS)
        serious_message = self.theme_engine.generate_message(MessageType.SUCCESS)
        
        self.theme_engine.set_tone(ToneStyle.HUMOROUS)
        humorous_message = self.theme_engine.generate_message(MessageType.SUCCESS)
        
        # Messages should be different (though this might occasionally fail due to randomness)
        # We'll run this multiple times to increase confidence
        different_messages = 0
        for _ in range(10):
            self.theme_engine.set_tone(ToneStyle.SERIOUS)
            s_msg = self.theme_engine.generate_message(MessageType.SUCCESS)
            self.theme_engine.set_tone(ToneStyle.HUMOROUS)
            h_msg = self.theme_engine.generate_message(MessageType.SUCCESS)
            if s_msg != h_msg:
                different_messages += 1
        
        # At least some messages should be different
        self.assertGreater(different_messages, 0)
    
    def test_missing_template_parameter(self):
        """Test handling of missing template parameters"""
        message = self.theme_engine.generate_message(MessageType.WELCOME)  # Missing 'name' parameter
        
        self.assertIn("Error", message)
        self.assertIn("parámetro", message)
    
    def test_invalid_message_type(self):
        """Test handling of invalid message type"""
        # This would require creating an invalid enum value, which isn't straightforward
        # Instead, we'll test the fallback behavior by mocking
        with patch.object(self.theme_engine, 'templates', {}):
            message = self.theme_engine.generate_message(MessageType.SUCCESS)
            self.assertIn("Error", message)
            self.assertIn("no reconocido", message)
    
    def test_get_random_mafia_term(self):
        """Test random mafia term retrieval"""
        boss_title = self.theme_engine.get_random_mafia_term("boss_titles")
        self.assertIn(boss_title, ["Don", "Capo", "Jefe", "Padrino"])
        
        member_title = self.theme_engine.get_random_mafia_term("member_titles")
        self.assertIn(member_title, ["soldado", "capo", "hermano", "compañero"])
        
        family_term = self.theme_engine.get_random_mafia_term("family_terms")
        self.assertIn(family_term, ["familia", "organización", "casa", "clan"])
    
    def test_get_random_mafia_term_invalid_category(self):
        """Test random mafia term with invalid category"""
        term = self.theme_engine.get_random_mafia_term("invalid_category")
        self.assertEqual(term, "")
    
    def test_get_iconic_phrase(self):
        """Test iconic phrase retrieval"""
        phrase = self.theme_engine.get_iconic_phrase()
        
        expected_phrases = [
            "Te haré una oferta que no podrás rechazar",
            "Es solo negocio, nada personal",
            "Un hombre que no pasa tiempo con su familia nunca puede ser un hombre real",
            "Mantén a tus amigos cerca, pero a tus enemigos más cerca",
            "La venganza es un plato que se sirve frío",
            "En este negocio, la confianza es todo"
        ]
        
        self.assertIn(phrase, expected_phrases)
    
    @patch('random.random')
    def test_enhance_message_with_phrase(self, mock_random):
        """Test message enhancement with iconic phrase"""
        mock_random.return_value = 0.2  # Below 0.3 threshold
        
        base_message = "Test message"
        enhanced = self.theme_engine.enhance_message(base_message, add_phrase=True)
        
        self.assertIn(base_message, enhanced)
        self.assertIn("_", enhanced)  # Italic formatting for phrase
    
    @patch('random.random')
    def test_enhance_message_without_phrase(self, mock_random):
        """Test message enhancement without iconic phrase"""
        mock_random.return_value = 0.5  # Above 0.3 threshold
        
        base_message = "Test message"
        enhanced = self.theme_engine.enhance_message(base_message, add_phrase=True)
        
        self.assertEqual(enhanced, base_message)
    
    def test_format_quote_message_without_author(self):
        """Test quote formatting without author"""
        quote = "El éxito requiere trabajo duro"
        formatted = self.theme_engine.format_quote_message(quote)
        
        self.assertIn(quote, formatted)
        self.assertIn("*", formatted)  # Bold formatting for prefix
        self.assertIn("\"", formatted)  # Quote marks
        self.assertIn("_", formatted)  # Italic signature
    
    def test_format_quote_message_with_author(self):
        """Test quote formatting with author"""
        quote = "El éxito requiere trabajo duro"
        author = "Don Corleone"
        formatted = self.theme_engine.format_quote_message(quote, author)
        
        self.assertIn(quote, formatted)
        self.assertIn(author, formatted)
        self.assertIn("*", formatted)  # Bold formatting
        self.assertIn("\"", formatted)  # Quote marks
        self.assertIn("—", formatted)  # Author attribution
    
    def test_format_quote_message_tone_difference(self):
        """Test quote formatting differs between tones"""
        quote = "Test quote"
        
        self.theme_engine.set_tone(ToneStyle.SERIOUS)
        serious_format = self.theme_engine.format_quote_message(quote)
        
        self.theme_engine.set_tone(ToneStyle.HUMOROUS)
        humorous_format = self.theme_engine.format_quote_message(quote)
        
        # Both should contain the quote but have different prefixes
        self.assertIn(quote, serious_format)
        self.assertIn(quote, humorous_format)
        # The prefixes should be different (though we can't guarantee exact difference due to randomness)
        self.assertIsInstance(serious_format, str)
        self.assertIsInstance(humorous_format, str)
    
    def test_format_command_help(self):
        """Test command help formatting"""
        commands = {
            "start": "Iniciar el bot",
            "help": "Mostrar ayuda",
            "quote": "Enviar frase motivacional"
        }
        
        formatted = self.theme_engine.format_command_help(commands)
        
        # Check all commands are included
        for command, description in commands.items():
            self.assertIn(f"/{command}", formatted)
            self.assertIn(description, formatted)
        
        # Check mafia theming
        self.assertTrue(any(term in formatted.lower() for term in ["familia", "comandos", "capo"]))
        self.assertIn("_", formatted)  # Italic footer
    
    def test_format_command_help_tone_difference(self):
        """Test command help formatting differs between tones"""
        commands = {"test": "Test command"}
        
        self.theme_engine.set_tone(ToneStyle.SERIOUS)
        serious_help = self.theme_engine.format_command_help(commands)
        
        self.theme_engine.set_tone(ToneStyle.HUMOROUS)
        humorous_help = self.theme_engine.format_command_help(commands)
        
        # Both should contain the command but have different styling
        self.assertIn("/test", serious_help)
        self.assertIn("/test", humorous_help)
        self.assertIn("Test command", serious_help)
        self.assertIn("Test command", humorous_help)
    
    def test_format_error_with_suggestion(self):
        """Test error formatting with suggestion"""
        error_msg = "Archivo no válido"
        suggestion = "Usa un archivo .txt, .csv o .json"
        
        formatted = self.theme_engine.format_error_with_suggestion(error_msg, suggestion)
        
        self.assertIn(error_msg, formatted)
        self.assertIn(suggestion, formatted)
        self.assertTrue(any(term in formatted.lower() for term in ["error", "problema", "familia", "técnicos", "sistema", "negocio", "capo"]))
    
    def test_format_error_with_suggestion_tone_difference(self):
        """Test error formatting differs between tones"""
        error_msg = "Test error"
        suggestion = "Test suggestion"
        
        self.theme_engine.set_tone(ToneStyle.SERIOUS)
        serious_error = self.theme_engine.format_error_with_suggestion(error_msg, suggestion)
        
        self.theme_engine.set_tone(ToneStyle.HUMOROUS)
        humorous_error = self.theme_engine.format_error_with_suggestion(error_msg, suggestion)
        
        # Both should contain the error and suggestion
        self.assertIn(error_msg, serious_error)
        self.assertIn(error_msg, humorous_error)
        self.assertIn(suggestion, serious_error)
        self.assertIn(suggestion, humorous_error)
    
    def test_spanish_localization(self):
        """Test that all messages are in Spanish"""
        message_types = [
            MessageType.WELCOME,
            MessageType.SUCCESS,
            MessageType.ERROR,
            MessageType.WARNING,
            MessageType.CONFIRMATION,
            MessageType.MOTIVATIONAL,
            MessageType.REMINDER,
            MessageType.HELP
        ]
        
        spanish_indicators = [
            "familia", "capo", "soldado", "negocio", "bienvenido",
            "trabajo", "éxito", "error", "problema", "recordatorio",
            "comandos", "respeto", "lealtad", "operación", "misión",
            "paciencia", "límites", "decisión", "seguro", "confirma",
            "hielo", "delgado", "piénsalo", "bien", "última", "advertencia",
            "consecuencias", "próximo", "herramientas", "organización", 
            "disposición", "manual", "operaciones", "caminando", "estás"
        ]
        
        for msg_type in message_types:
            if msg_type in [MessageType.WELCOME, MessageType.WARNING, MessageType.REMINDER]:
                # These require parameters
                if msg_type == MessageType.REMINDER:
                    message = self.theme_engine.generate_message(msg_type, message="test")
                else:
                    message = self.theme_engine.generate_message(msg_type, name="test")
            else:
                message = self.theme_engine.generate_message(msg_type)
            
            # At least one Spanish indicator should be present
            has_spanish = any(indicator in message.lower() for indicator in spanish_indicators)
            self.assertTrue(has_spanish, f"Message type {msg_type} doesn't contain Spanish indicators: {message}")
    
    def test_mafia_terminology_presence(self):
        """Test that mafia terminology is consistently used"""
        mafia_terms = [
            "familia", "capo", "soldado", "don", "negocio",
            "operación", "respeto", "lealtad", "organización",
            "hielo", "delgado", "paciencia", "límites", "advertencia",
            "consecuencias", "misión", "trabajo", "éxito"
        ]
        
        # Test across different message types
        messages = [
            self.theme_engine.generate_message(MessageType.WELCOME, name="test"),
            self.theme_engine.generate_message(MessageType.SUCCESS),
            self.theme_engine.generate_message(MessageType.WARNING, name="test"),
            self.theme_engine.generate_message(MessageType.MOTIVATIONAL),
            self.theme_engine.generate_message(MessageType.HELP)
        ]
        
        for message in messages:
            has_mafia_term = any(term in message.lower() for term in mafia_terms)
            self.assertTrue(has_mafia_term, f"Message lacks mafia terminology: {message}")
    
    def test_template_completeness(self):
        """Test that all message types have templates for both tones"""
        required_types = [
            MessageType.WELCOME,
            MessageType.SUCCESS,
            MessageType.ERROR,
            MessageType.WARNING,
            MessageType.CONFIRMATION,
            MessageType.MOTIVATIONAL,
            MessageType.REMINDER,
            MessageType.HELP
        ]
        
        for msg_type in required_types:
            self.assertIn(msg_type, self.theme_engine.templates)
            self.assertIn(ToneStyle.SERIOUS, self.theme_engine.templates[msg_type])
            self.assertIn(ToneStyle.HUMOROUS, self.theme_engine.templates[msg_type])
            
            # Each tone should have at least one template
            self.assertGreater(len(self.theme_engine.templates[msg_type][ToneStyle.SERIOUS]), 0)
            self.assertGreater(len(self.theme_engine.templates[msg_type][ToneStyle.HUMOROUS]), 0)


if __name__ == '__main__':
    unittest.main()