"""
Mafia Theme Engine for @donhustle_bot

This module provides a centralized system for generating mafia-themed messages
with support for tone adjustment and Spanish localization.
"""

from enum import Enum
from typing import Dict, List, Optional, Any
import random


class ToneStyle(Enum):
    """Tone styles for bot responses"""
    SERIOUS = "serio"
    HUMOROUS = "humorístico"


class MessageType(Enum):
    """Types of messages the bot can send"""
    WELCOME = "welcome"
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"
    CONFIRMATION = "confirmation"
    MOTIVATIONAL = "motivational"
    REMINDER = "reminder"
    HELP = "help"


class ThemeEngine:
    """
    Mafia-themed message generation engine with template-based responses
    and tone adjustment capabilities.
    """
    
    def __init__(self, default_tone: ToneStyle = ToneStyle.SERIOUS):
        self.current_tone = default_tone
        self._initialize_templates()
    
    def _initialize_templates(self):
        """Initialize message templates for different contexts and tones"""
        self.templates = {
            MessageType.WELCOME: {
                ToneStyle.SERIOUS: [
                    "Bienvenido a la familia, {name}. Aquí trabajamos duro y respetamos el negocio.",
                    "Un nuevo soldado se une a nuestra familia. Bienvenido, {name}.",
                    "La familia crece. Bienvenido, {name}. Que tu trabajo honre nuestro nombre.",
                    "Bienvenido a nuestro círculo, {name}. Aquí el respeto se gana con dedicación."
                ],
                ToneStyle.HUMOROUS: [
                    "¡Eh, {name}! Otro valiente se atreve a entrar en nuestro territorio. ¡Bienvenido!",
                    "Mira quién decidió unirse al circo, digo... a la familia. ¡Bienvenido, {name}!",
                    "¡{name}! Te haré una oferta que no podrás rechazar... ¡quedarte en este grupo!",
                    "Un nuevo pez en nuestro acuario. Espero que sepas nadar, {name}. ¡Bienvenido!"
                ]
            },
            MessageType.SUCCESS: {
                ToneStyle.SERIOUS: [
                    "Excelente trabajo, capo. La familia está orgullosa.",
                    "Misión cumplida. Así es como se hace el negocio, soldado.",
                    "Perfecto, capo. Tu lealtad a la familia no pasa desapercibida.",
                    "Trabajo bien hecho, soldado. La familia reconoce tu dedicación."
                ],
                ToneStyle.HUMOROUS: [
                    "¡Bravo, capo! Hasta Don Corleone estaría impresionado.",
                    "¡Excelente trabajo, soldado! Mereces un aplauso... y tal vez un cannoli.",
                    "¡Fantástico, capo! Eres más eficiente que nuestro contador de la familia.",
                    "¡Perfecto, soldado! Te ganaste un lugar en la mesa principal de la familia."
                ]
            },
            MessageType.ERROR: {
                ToneStyle.SERIOUS: [
                    "Algo salió mal en el negocio, capo. Inténtalo de nuevo.",
                    "Los libros de la familia están ocupados. Inténtalo en un momento.",
                    "Hubo un problema con la operación. La familia lo resolverá pronto.",
                    "Error en el sistema, capo. Nuestros técnicos están en ello."
                ],
                ToneStyle.HUMOROUS: [
                    "¡Oops! Parece que alguien tropezó con los cables. Inténtalo de nuevo, capo.",
                    "Error 404: La mafia no encontró lo que buscas. ¡Ja!",
                    "Algo se rompió, pero no fueron las piernas de nadie. Inténtalo otra vez.",
                    "Houston, tenemos un problema... digo, Don Corleone, tenemos un problema."
                ]
            },
            MessageType.WARNING: {
                ToneStyle.SERIOUS: [
                    "Cuidado, {name}. La familia no tolera la falta de respeto.",
                    "Última advertencia, {name}. El próximo error tendrá consecuencias.",
                    "Estás caminando en hielo delgado, {name}. Piénsalo bien.",
                    "La paciencia de la familia tiene límites, {name}."
                ],
                ToneStyle.HUMOROUS: [
                    "¡Eh, {name}! Estás nadando con tiburones. Ten cuidado.",
                    "Cuidadito, {name}. No querrás despertar al Don que llevo dentro.",
                    "¡{name}! Estás jugando con fuego... y tenemos muchos fósforos.",
                    "Atención {name}: estás a un paso de dormir con los peces... digitales."
                ]
            },
            MessageType.CONFIRMATION: {
                ToneStyle.SERIOUS: [
                    "¿Estás seguro de esta decisión, capo? No hay vuelta atrás.",
                    "Confirma tu elección. La familia necesita estar segura.",
                    "¿Proceder con la operación? Responde sí o no.",
                    "Última oportunidad para reconsiderar, soldado."
                ],
                ToneStyle.HUMOROUS: [
                    "¿Seguro, seguro? No queremos lamentos después, capo.",
                    "¿Estás 100% convencido? Porque después no acepto quejas.",
                    "¿Confirmas? Una vez que aprietes el botón, no hay ctrl+z en la mafia.",
                    "¿Procedemos? Recuerda: en la familia no hay devoluciones."
                ]
            },
            MessageType.MOTIVATIONAL: {
                ToneStyle.SERIOUS: [
                    "El éxito se construye con trabajo duro y determinación, capo.",
                    "La familia prospera cuando cada soldado da lo mejor de sí.",
                    "No hay atajos en el camino al éxito. Solo trabajo y dedicación.",
                    "La grandeza se forja en la disciplina diaria, soldado."
                ],
                ToneStyle.HUMOROUS: [
                    "¡Arriba, capo! Los cannolis no se van a ganar solos.",
                    "¡A trabajar! Que Don Corleone no construyó su imperio viendo Netflix.",
                    "¡Dale que se puede! Hasta Al Capone empezó desde abajo.",
                    "¡Vamos! La familia necesita soldados, no sofás con patas."
                ]
            },
            MessageType.REMINDER: {
                ToneStyle.SERIOUS: [
                    "Recordatorio de la familia: {message}",
                    "No olvides, capo: {message}",
                    "La familia te recuerda: {message}",
                    "Importante para el negocio: {message}"
                ],
                ToneStyle.HUMOROUS: [
                    "¡Ring ring! Tu recordatorio mafioso: {message}",
                    "¡Despierta, bella durmiente! Recordatorio: {message}",
                    "El Don te recuerda (con cariño): {message}",
                    "¡Atención soldado distraído! {message}"
                ]
            },
            MessageType.HELP: {
                ToneStyle.SERIOUS: [
                    "La familia está aquí para ayudarte, capo. Estos son los comandos disponibles:",
                    "Comandos de la familia para hacer el negocio:",
                    "Herramientas de la organización a tu disposición:",
                    "Manual de operaciones de la familia:"
                ],
                ToneStyle.HUMOROUS: [
                    "¡Manual de supervivencia en la mafia digital! Comandos disponibles:",
                    "¿Perdido, capo? Aquí tienes la guía de la familia:",
                    "¡SOS! Manual de emergencia para soldados despistados:",
                    "Comandos para no hacer el ridículo en la familia:"
                ]
            }
        }
        
        # Mafia terminology and phrases
        self.mafia_terms = {
            "boss_titles": ["Don", "Capo", "Jefe", "Padrino"],
            "member_titles": ["soldado", "capo", "hermano", "compañero"],
            "family_terms": ["familia", "organización", "casa", "clan"],
            "business_terms": ["negocio", "operación", "trabajo", "misión"],
            "respect_terms": ["respeto", "honor", "lealtad", "disciplina"],
            "threat_terms": ["consecuencias", "dormir con los peces", "nadar con tiburones", "hielo delgado"]
        }
        
        # Iconic phrases
        self.iconic_phrases = [
            "Te haré una oferta que no podrás rechazar",
            "Es solo negocio, nada personal",
            "Un hombre que no pasa tiempo con su familia nunca puede ser un hombre real",
            "Mantén a tus amigos cerca, pero a tus enemigos más cerca",
            "La venganza es un plato que se sirve frío",
            "En este negocio, la confianza es todo"
        ]
    
    def set_tone(self, tone: ToneStyle):
        """Set the current tone style for message generation"""
        self.current_tone = tone
    
    def get_tone(self) -> ToneStyle:
        """Get the current tone style"""
        return self.current_tone
    
    def generate_message(self, message_type: MessageType, **kwargs) -> str:
        """
        Generate a themed message based on type and current tone
        
        Args:
            message_type: Type of message to generate
            **kwargs: Template variables (name, message, etc.)
            
        Returns:
            Formatted mafia-themed message
        """
        if message_type not in self.templates:
            return "Error: Tipo de mensaje no reconocido por la familia."
        
        tone_templates = self.templates[message_type].get(self.current_tone, [])
        if not tone_templates:
            # Fallback to serious tone if current tone not available
            tone_templates = self.templates[message_type].get(ToneStyle.SERIOUS, [])
        
        if not tone_templates:
            return "Error: No hay plantillas disponibles para este tipo de mensaje."
        
        template = random.choice(tone_templates)
        
        try:
            return template.format(**kwargs)
        except KeyError as e:
            return f"Error: Falta el parámetro {e} para generar el mensaje."
    
    def get_random_mafia_term(self, category: str) -> str:
        """Get a random mafia term from a specific category"""
        terms = self.mafia_terms.get(category, [])
        return random.choice(terms) if terms else ""
    
    def get_iconic_phrase(self) -> str:
        """Get a random iconic mafia phrase"""
        return random.choice(self.iconic_phrases)
    
    def enhance_message(self, base_message: str, add_phrase: bool = False) -> str:
        """
        Enhance a message with mafia terminology and optional iconic phrase
        
        Args:
            base_message: Base message to enhance
            add_phrase: Whether to add an iconic phrase
            
        Returns:
            Enhanced message with mafia theming
        """
        enhanced = base_message
        
        if add_phrase and random.random() < 0.3:  # 30% chance to add iconic phrase
            enhanced += f"\n\n_{self.get_iconic_phrase()}_"
        
        return enhanced
    
    def format_quote_message(self, quote: str, author: Optional[str] = None) -> str:
        """Format a motivational quote with mafia theming"""
        if self.current_tone == ToneStyle.SERIOUS:
            prefix = random.choice([
                "Palabras de sabiduría para la familia:",
                "El Don comparte su sabiduría:",
                "Reflexión para los soldados:",
                "Sabiduría de la organización:"
            ])
        else:
            prefix = random.choice([
                "¡Atención soldados! Momento de inspiración:",
                "El Don habla (y más vale que escuchen):",
                "¡Dosis de motivación mafiosa!",
                "Sabiduría directa desde Sicilia:"
            ])
        
        formatted_quote = f"*{prefix}*\n\n\"{quote}\""
        
        if author:
            formatted_quote += f"\n\n— {author}"
        
        # Add mafia signature
        signature = random.choice([
            "\n\n_La familia que trabaja junta, prospera junta._",
            "\n\n_— Don Hustle y la familia_",
            "\n\n_Que estas palabras guíen tu camino, capo._"
        ])
        
        return formatted_quote + signature
    
    def format_command_help(self, commands: Dict[str, str]) -> str:
        """Format command help with mafia theming"""
        help_intro = self.generate_message(MessageType.HELP)
        
        formatted_commands = []
        for command, description in commands.items():
            formatted_commands.append(f"/{command} - {description}")
        
        help_text = f"{help_intro}\n\n" + "\n".join(formatted_commands)
        
        if self.current_tone == ToneStyle.HUMOROUS:
            help_text += "\n\n_¡Úsalos sabiamente, o Don Corleone se enfadará!_"
        else:
            help_text += "\n\n_Usa estos comandos con respeto y responsabilidad._"
        
        return help_text
    
    def format_error_with_suggestion(self, error_message: str, suggestion: str) -> str:
        """Format error message with helpful suggestion"""
        base_error = self.generate_message(MessageType.ERROR)
        
        if self.current_tone == ToneStyle.SERIOUS:
            return f"{base_error}\n\n*Detalles:* {error_message}\n*Sugerencia:* {suggestion}"
        else:
            return f"{base_error}\n\n*¿Qué pasó?* {error_message}\n*¿Qué hacer?* {suggestion}"