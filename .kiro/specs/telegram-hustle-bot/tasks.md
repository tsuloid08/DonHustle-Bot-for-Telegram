# Implementation Plan

- [x] 1. Set up project structure and core dependencies





  - Create directory structure for handlers, database, utils, and tests
  - Set up Python virtual environment and install python-telegram-bot library
  - Create requirements.txt with all necessary dependencies
  - Initialize git repository with appropriate .gitignore
  - _Requirements: 11.3_

- [x] 2. Implement database layer and models




  - [x] 2.1 Create database schema and connection manager


    - Write SQL schema for all tables (quotes, saved_messages, reminders, user_activity, custom_commands, config, spam_filters)
    - Implement DatabaseManager class with connection handling and initialization
    - Create database migration system for schema updates
    - _Requirements: 3.1, 3.2, 5.1, 6.1, 7.1, 8.1, 9.1_
  
  - [x] 2.2 Implement data models and repositories


    - Create dataclass models for Quote, Reminder, SavedMessage, and other entities
    - Implement QuoteRepository with CRUD operations for quote management
    - Implement MessageRepository for saved message operations
    - Implement ReminderRepository for reminder scheduling and retrieval
    - Implement ConfigRepository for bot configuration management
    - Write unit tests for all repository classes
    - _Requirements: 3.1, 3.2, 4.1, 5.1, 6.1, 7.1, 9.1_

- [x] 3. Create mafia theme engine









  - Implement ThemeEngine class with template-based message generation
  - Create message templates for all bot responses with mafia terminology
  - Implement tone adjustment system (serious/humorous) as specified in requirements
  - Add Spanish localization support for mafia phrases and responses
  - Write unit tests for theme engine with various message scenarios
  - _Requirements: 1.1, 1.2, 1.3, 11.1_

- [x] 4. Implement core bot application and basic commands







  - [x] 4.1 Create main bot application structure




    - Implement bot.py with Application setup and token configuration
    - Create handler registration system for modular command handling
    - Implement basic error handling with mafia-themed error messages
    - Add logging configuration for debugging and monitoring
    - _Requirements: 11.2, 11.3_
  
  - [x] 4.2 Implement basic command handlers


    - Create CommandHandler base class for consistent command processing
    - Implement /start command with help information and mafia-themed welcome
    - Implement /rules command displaying group rules with hustle culture principles
    - Write unit tests for basic command functionality
    - _Requirements: 2.3, 11.2_

- [x] 5. Implement welcome and group management features





  - Implement /welcome command for configurable welcome message setup
  - Create new member detection and automatic welcome message sending
  - Implement welcome message storage and retrieval from database
  - Add mafia-themed default welcome message template
  - Write integration tests for welcome message flow
  - _Requirements: 2.1, 2.2_

- [-] 6. Implement file processing system for quote uploads


  - [x] 6.1 Create file processing utilities


    - Implement FileProcessor class supporting .txt, .csv, and .json formats
    - Create parse_txt method for line-by-line quote extraction
    - Create parse_csv method using pandas for quote column extraction
    - Create parse_json method for JSON array parsing
    - Add file validation and error handling with mafia-themed error messages
    - _Requirements: 3.1, 3.2, 3.3, 3.4_
  
  - [x] 6.2 Implement quote upload command


    - Create /uploadquotes command handler for file processing
    - Implement file download from Telegram API using context.bot.get_file()
    - Integrate FileProcessor with quote database storage
    - Add success confirmation with "Capo, las frases han sido añadidas al libro de la familia"
    - Write integration tests for file upload workflow
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [x] 7. Implement quote management system




  - [x] 7.1 Create quote display and management commands


    - Implement /listquotes command showing all quotes with indices
    - Implement /deletequote command for removing specific quotes by index
    - Implement /clearquotes command with confirmation dialog
    - Implement /addhustle command for adding single quotes
    - Write unit tests for all quote management operations
    - _Requirements: 4.1, 4.2, 4.3, 4.4_
  
  - [x] 7.2 Implement automatic quote sending system


    - Create message counter system tracking group message count
    - Implement /setquoteinterval command for configuring quote frequency
    - Create automatic quote sending when message count reaches interval
    - Implement /hustle and /motivate commands for immediate quote sending
    - Add random quote selection from database
    - Write integration tests for automatic quote system
    - _Requirements: 3.6, 3.7, 3.8_

- [-] 8. Implement message tagging and saving system




















  - [x] 8.1 Create message tagging functionality


    - Implement /tag command for tagging messages with specified labels
    - Create message storage with tag association in database
    - Implement /searchtag command for retrieving tagged messages
    - Add mafia-themed responses for tagging operations
    - _Requirements: 5.1, 5.2, 5.3_
  


  - [ ] 8.2 Create message saving system
    - Implement /save command for storing important messages
    - Create message storage system supporting message ID and content
    - Implement /savedmessages command for listing saved messages
    - Add mafia-themed presentation for saved message display
    - Write unit tests for message saving and retrieval
    - _Requirements: 6.1, 6.2, 6.3_

- [ ] 9. Implement reminder system with scheduling
  - [ ] 9.1 Create reminder scheduling functionality
    - Implement /remind command parsing date, time, and message parameters
    - Create reminder storage in database with proper datetime handling
    - Implement recurring reminder support with /remind weekly syntax
    - Add reminder validation and error handling
    - _Requirements: 7.1, 7.3_
  
  - [ ] 9.2 Create reminder execution system
    - Implement background scheduler for checking due reminders
    - Create reminder notification system with mafia-themed messages
    - Implement /reminders command for listing active reminders
    - Add reminder cleanup for completed one-time reminders
    - Write integration tests for reminder scheduling and execution
    - _Requirements: 7.2, 7.4_

- [ ] 10. Implement inactive user management system
  - [ ] 10.1 Create user activity tracking
    - Implement user activity monitoring for all message types
    - Create user_activity table updates on every user message
    - Implement /setinactive command for configuring inactivity threshold
    - Add activity timestamp tracking and database storage
    - _Requirements: 8.3_
  
  - [ ] 10.2 Create inactive user detection and removal
    - Implement background task for checking inactive users
    - Create warning system for users approaching inactivity limit
    - Implement automatic user removal after warning period expires
    - Add /disableinactive command for disabling automatic removal
    - Create mafia-themed warning messages about "sleeping with fishes"
    - Write integration tests for inactive user management workflow
    - _Requirements: 8.1, 8.2, 8.4, 8.5_

- [ ] 11. Implement anti-spam and moderation features
  - Implement spam detection system with configurable word filters
  - Create /filter add command for adding spam filter words
  - Implement automatic message deletion for detected spam
  - Add user warning system with mafia-themed messages about "swimming with sharks"
  - Create moderation action logging and user strike system
  - Write unit tests for spam detection and moderation actions
  - _Requirements: 10.1, 10.2, 10.3, 10.4_

- [ ] 12. Implement custom commands system
  - Implement /addcommand command for creating custom bot commands
  - Create custom command storage and retrieval from database
  - Implement dynamic command handler registration for custom commands
  - Add /customcommands command for listing available custom commands
  - Create custom command execution with stored responses
  - Write unit tests for custom command creation and execution
  - _Requirements: 9.1, 9.2, 9.3_

- [ ] 13. Implement bot configuration and style management
  - Implement /setstyle command for adjusting bot tone (serious/humorous)
  - Create configuration storage system for per-chat settings
  - Integrate style settings with ThemeEngine for dynamic response adjustment
  - Add bot permission validation for administrative commands
  - Create configuration validation and error handling
  - Write unit tests for configuration management
  - _Requirements: 11.1, 11.4_

- [ ] 14. Create comprehensive test suite
  - [ ] 14.1 Write unit tests for all components
    - Create test fixtures for database operations with in-memory SQLite
    - Write unit tests for all command handlers with mock Telegram updates
    - Create unit tests for file processing with sample files
    - Add unit tests for theme engine message generation
    - _Requirements: All requirements for testing coverage_
  
  - [ ] 14.2 Create integration tests
    - Write end-to-end tests for complete command workflows
    - Create integration tests for database operations with real SQLite
    - Add integration tests for file upload and processing
    - Create tests for scheduler and background task functionality
    - _Requirements: All requirements for integration testing_

- [ ] 15. Implement deployment configuration
  - Create environment variable configuration for bot token and settings
  - Implement production database setup with persistent storage
  - Create Docker configuration for containerized deployment
  - Add process monitoring and automatic restart configuration
  - Create deployment documentation with setup instructions
  - _Requirements: 11.3_

- [ ] 16. Add error handling and logging
  - Implement comprehensive error handling for all bot operations
  - Create mafia-themed error messages for all error scenarios
  - Add structured logging for debugging and monitoring
  - Implement graceful degradation for non-critical feature failures
  - Create error recovery mechanisms for database and API failures
  - _Requirements: 11.3_