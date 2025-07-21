# Requirements Document

## Introduction

@donhustle_bot is a Telegram bot designed to manage private groups with advanced moderation, automation, and organization features. The bot embodies a mafia-inspired theme from "The Godfather" with a charismatic, authoritative, and elegant tone, using terms like "capo", "familia", "negocio", and iconic phrases like "Te haré una oferta que no podrás rechazar". The bot combines hustle culture (hard work mentality, ambition, and productivity) with a mafia aesthetic to maintain active, organized, and focused groups.

## Requirements

### Requirement 1: Bot Identity and Theme

**User Story:** As a group administrator, I want the bot to have a consistent mafia-inspired personality, so that it creates an engaging and memorable experience for group members.

#### Acceptance Criteria

1. WHEN the bot responds to any command THEN the bot SHALL use mafia-inspired language including terms like "capo", "familia", "negocio"
2. WHEN the bot sends messages THEN the bot SHALL maintain a charismatic, authoritative, and elegant tone
3. WHEN appropriate THEN the bot SHALL include iconic phrases like "Te haré una oferta que no podrás rechazar"
4. WHEN the bot is configured THEN the bot SHALL have a profile picture of a mafioso with fedora, dark suit, and cigar

### Requirement 2: Group Welcome and Rules Management

**User Story:** As a group administrator, I want to configure welcome messages and rules, so that new members understand group expectations immediately.

#### Acceptance Criteria

1. WHEN a new member joins the group THEN the bot SHALL send a configurable welcome message with mafia-themed language
2. WHEN an administrator uses /welcome [mensaje] THEN the bot SHALL save the custom welcome message
3. WHEN someone uses /rules THEN the bot SHALL display the group rules with mafia-themed presentation
4. WHEN displaying rules THEN the bot SHALL include default hustle culture principles: work hard, no spam, loyalty to the business

### Requirement 3: Motivational Quote System

**User Story:** As a group administrator, I want to upload and manage motivational quotes, so that the bot can automatically inspire members with hustle culture messages.

#### Acceptance Criteria

1. WHEN an administrator uses /uploadquotes with a file THEN the bot SHALL accept .txt, .csv, and .json formats
2. WHEN processing .txt files THEN the bot SHALL treat each line as a separate quote
3. WHEN processing .csv files THEN the bot SHALL extract quotes from the "quote" column
4. WHEN processing .json files THEN the bot SHALL extract quotes from a JSON array
5. WHEN quotes are uploaded successfully THEN the bot SHALL confirm with "Capo, las frases han sido añadidas al libro de la familia"
6. WHEN /setquoteinterval [número] is used THEN the bot SHALL configure automatic quote sending every X messages
7. WHEN the message count reaches the interval THEN the bot SHALL send a random motivational quote
8. WHEN /hustle or /motivate is used THEN the bot SHALL send a random motivational quote immediately

### Requirement 4: Quote Management

**User Story:** As a group administrator, I want to manage the quote database, so that I can maintain quality and relevance of motivational content.

#### Acceptance Criteria

1. WHEN /listquotes is used THEN the bot SHALL display all stored quotes with indices
2. WHEN /deletequote [índice] is used THEN the bot SHALL remove the specified quote
3. WHEN /clearquotes is used THEN the bot SHALL request confirmation before deleting all quotes
4. WHEN /addhustle [frase] is used THEN the bot SHALL add a single quote to the database

### Requirement 5: Message Tagging System

**User Story:** As a group member, I want to tag and search messages, so that I can organize and find important content easily.

#### Acceptance Criteria

1. WHEN /tag [etiqueta] is used on a message THEN the bot SHALL save the message with the specified tag
2. WHEN /searchtag [etiqueta] is used THEN the bot SHALL return all messages with that tag
3. WHEN displaying tagged messages THEN the bot SHALL include mafia-themed language like "negocios etiquetados"

### Requirement 6: Message Saving System

**User Story:** As a group member, I want to save important messages, so that I can reference them later.

#### Acceptance Criteria

1. WHEN /save [mensaje o ID] is used THEN the bot SHALL store the specified message
2. WHEN /savedmessages is used THEN the bot SHALL display all saved messages
3. WHEN displaying saved messages THEN the bot SHALL use mafia-themed language like "negocios importantes que la familia necesita recordar"

### Requirement 7: Reminder System

**User Story:** As a group member, I want to set reminders, so that I don't forget important tasks or events.

#### Acceptance Criteria

1. WHEN /remind [fecha] [hora] [mensaje] is used THEN the bot SHALL schedule a reminder for the specified time
2. WHEN a reminder time arrives THEN the bot SHALL send the reminder message with mafia-themed language
3. WHEN /remind weekly [día] [hora] [mensaje] is used THEN the bot SHALL create a recurring weekly reminder
4. WHEN /reminders is used THEN the bot SHALL list all active reminders

### Requirement 8: Inactive User Management

**User Story:** As a group administrator, I want to automatically manage inactive users, so that the group remains active and engaged.

#### Acceptance Criteria

1. WHEN a user hasn't sent messages for 7 days (configurable) THEN the bot SHALL send a warning message
2. WHEN the warning period expires (24 hours) AND the user remains inactive THEN the bot SHALL remove the user from the group
3. WHEN /setinactive [días] is used THEN the bot SHALL update the inactivity threshold
4. WHEN /disableinactive is used THEN the bot SHALL disable automatic inactive user removal
5. WHEN warning inactive users THEN the bot SHALL use threatening mafia language about "sleeping with the fishes"

### Requirement 9: Custom Commands

**User Story:** As a group administrator, I want to create custom commands, so that I can add personalized functionality to the bot.

#### Acceptance Criteria

1. WHEN /addcommand [nombre] [respuesta] is used THEN the bot SHALL create a new custom command
2. WHEN a custom command is invoked THEN the bot SHALL respond with the configured message
3. WHEN /customcommands is used THEN the bot SHALL list all available custom commands

### Requirement 10: Anti-Spam and Moderation

**User Story:** As a group administrator, I want automatic spam detection and moderation, so that the group maintains quality discussions.

#### Acceptance Criteria

1. WHEN spam is detected THEN the bot SHALL delete the spam message
2. WHEN spam is detected THEN the bot SHALL warn the user with mafia-themed language about "swimming with sharks"
3. WHEN /filter add [palabra] is used THEN the bot SHALL add the word to the spam filter
4. WHEN filtered words are used THEN the bot SHALL take appropriate moderation action

### Requirement 11: Bot Configuration and Style

**User Story:** As a group administrator, I want to configure the bot's behavior and style, so that it fits the group's preferences.

#### Acceptance Criteria

1. WHEN /setstyle [serio/humorístico] is used THEN the bot SHALL adjust its tone accordingly
2. WHEN /start is used THEN the bot SHALL display help information and available commands
3. WHEN the bot encounters errors THEN the bot SHALL handle them gracefully with mafia-themed error messages
4. WHEN the bot is added to a group THEN the bot SHALL require administrator permissions for moderation features