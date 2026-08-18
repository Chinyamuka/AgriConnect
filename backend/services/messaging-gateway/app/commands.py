"""
SMS Command Parser.

This module parses raw SMS text into structured commands.
It handles different command formats and extracts arguments.
"""
import re
from typing import Optional, Tuple, List
from app.models import Command, ParsedCommand, Language


class CommandParser:
    """
    Parse SMS text into commands.
    
    Supported commands:
    - SELL tomatoes 100kg K2500 Mkushi
    - LIST tomatoes Lusaka
    - BID 123 K3000
    - ACCEPT 456
    - PAY 789
    - CONFIRM 789
    - RATE 1 5 "Great farmer!"
    - PRICE tomatoes Lusaka
    - HELP
    - STATUS 789
    """
    
    def __init__(self):
        """Initialize the parser with command patterns."""
        self.command_patterns = {
            Command.SELL: self._parse_sell,
            Command.LIST: self._parse_list,
            Command.BID: self._parse_bid,
            Command.ACCEPT: self._parse_accept,
            Command.PAY: self._parse_pay,
            Command.CONFIRM: self._parse_confirm,
            Command.RATE: self._parse_rate,
            Command.PRICE: self._parse_price,
            Command.HELP: self._parse_help,
            Command.STATUS: self._parse_status,
        }
    
    def parse(self, text: str, phone: str) -> Optional[ParsedCommand]:
        """
        Parse raw SMS text into a command.
        
        Args:
            text: Raw SMS text
            phone: Sender's phone number
        
        Returns:
            ParsedCommand or None if invalid
        """
        # Clean the text
        text = text.strip().upper()
        
        # Detect language (could be in local language)
        language = self._detect_language(text)
        
        # Extract the command (first word)
        words = text.split()
        if not words:
            return None
        
        # Check if first word is a command
        try:
            command = Command(words[0])
        except ValueError:
            return None
        
        # Parse using the specific parser for this command
        parser = self.command_patterns.get(command)
        if parser:
            args = parser(text, words)
            if args is not None:
                return ParsedCommand(
                    command=command,
                    args=args,
                    phone=phone,
                    raw_text=text,
                    language=language
                )
        
        return None
    
    # ========================================================================
    # COMMAND PARSERS
    # ========================================================================
    
    def _parse_sell(self, text: str, words: List[str]) -> Optional[List[str]]:
        """
        Parse SELL command.
        
        Format: SELL <produce> <quantity><unit> <price> <district>
        Example: SELL tomatoes 100kg K2500 Mkushi
        
        Returns:
            [produce, quantity, unit, price, district]
        """
        if len(words) < 5:
            return None
        
        # Extract produce (word 1)
        produce = words[1]
        
        # Extract quantity and unit (word 2)
        quantity_match = re.match(r'(\d+)(kg|ton|bundle)?', words[2])
        if not quantity_match:
            return None
        
        quantity = quantity_match.group(1)
        unit = quantity_match.group(2) or "kg"
        
        # Extract price (word 3) - should start with K
        price = words[3]
        if price.startswith('K'):
            price = price[1:]
        
        # Extract district (word 4 and rest)
        district = ' '.join(words[4:])
        
        return [produce, quantity, unit, price, district]
    
    def _parse_list(self, text: str, words: List[str]) -> Optional[List[str]]:
        """
        Parse LIST command.
        
        Format: LIST [produce] [district]
        Example: LIST tomatoes Lusaka
        Example: LIST tomatoes
        Example: LIST
        
        Returns:
            [produce (optional), district (optional)]
        """
        args = []
        if len(words) > 1:
            args.append(words[1])
        if len(words) > 2:
            args.append(' '.join(words[2:]))
        return args
    
    def _parse_bid(self, text: str, words: List[str]) -> Optional[List[str]]:
        """
        Parse BID command.
        
        Format: BID <listing_id> <amount>
        Example: BID 123 K3000
        
        Returns:
            [listing_id, amount]
        """
        if len(words) < 3:
            return None
        
        listing_id = words[1]
        amount = words[2]
        if amount.startswith('K'):
            amount = amount[1:]
        
        return [listing_id, amount]
    
    def _parse_accept(self, text: str, words: List[str]) -> Optional[List[str]]:
        """
        Parse ACCEPT command.
        
        Format: ACCEPT <bid_id>
        Example: ACCEPT 456
        
        Returns:
            [bid_id]
        """
        if len(words) < 2:
            return None
        return [words[1]]
    
    def _parse_pay(self, text: str, words: List[str]) -> Optional[List[str]]:
        """
        Parse PAY command.
        
        Format: PAY <transaction_id>
        Example: PAY 789
        
        Returns:
            [transaction_id]
        """
        if len(words) < 2:
            return None
        return [words[1]]
    
    def _parse_confirm(self, text: str, words: List[str]) -> Optional[List[str]]:
        """
        Parse CONFIRM command.
        
        Format: CONFIRM <transaction_id>
        Example: CONFIRM 789
        
        Returns:
            [transaction_id]
        """
        if len(words) < 2:
            return None
        return [words[1]]
    
    def _parse_rate(self, text: str, words: List[str]) -> Optional[List[str]]:
        """
        Parse RATE command.
        
        Format: RATE <user_id> <score> [comment]
        Example: RATE 1 5 Great farmer!
        
        Returns:
            [user_id, score, comment]
        """
        if len(words) < 3:
            return None
        
        user_id = words[1]
        score = words[2]
        comment = ' '.join(words[3:]) if len(words) > 3 else ''
        
        return [user_id, score, comment]
    
    def _parse_price(self, text: str, words: List[str]) -> Optional[List[str]]:
        """
        Parse PRICE command.
        
        Format: PRICE <produce> [district]
        Example: PRICE tomatoes Lusaka
        
        Returns:
            [produce, district (optional)]
        """
        if len(words) < 2:
            return None
        
        produce = words[1]
        district = ' '.join(words[2:]) if len(words) > 2 else ''
        
        return [produce, district]
    
    def _parse_help(self, text: str, words: List[str]) -> Optional[List[str]]:
        """Parse HELP command - returns empty list."""
        return []
    
    def _parse_status(self, text: str, words: List[str]) -> Optional[List[str]]:
        """
        Parse STATUS command.
        
        Format: STATUS [transaction_id]
        Example: STATUS 789
        """
        return words[1:] if len(words) > 1 else []
    
    # ========================================================================
    # LANGUAGE DETECTION
    # ========================================================================
    
    def _detect_language(self, text: str) -> Language:
        """
        Detect the language of the SMS text.
        
        In a real implementation, this would use NLP or keywords.
        For now, we'll assume English.
        """
        # TODO: Implement language detection with NLP
        # Look for keywords in local languages
        return Language.ENGLISH


# Create a singleton instance
command_parser = CommandParser()
