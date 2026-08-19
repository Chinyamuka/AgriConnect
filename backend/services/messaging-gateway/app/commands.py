"""
SMS Command Parser with Location Mapping.
"""
import re
from typing import Optional, Tuple, List, Dict
from app.models import Command, ParsedCommand, Language


class CommandParser:
    """
    Parse SMS text into commands with location mapping.
    """
    
    # Simple district to lat/lng mapping (you'll need to expand this)
    DISTRICT_LOCATIONS: Dict[str, Tuple[float, float]] = {
        "lusaka": (-15.3875, 28.3228),
        "mkushi": (-13.5333, 29.7833),
        "kabwe": (-14.4333, 28.4333),
        "chipata": (-13.6333, 32.6333),
        "solwezi": (-12.1833, 26.4000),
        "ndola": (-12.9686, 28.6324),
        "kitwe": (-12.8024, 28.2132),
        "livingstone": (-17.8500, 25.8500),
        "kasama": (-10.2000, 31.1667),
        "mongu": (-15.2833, 23.1333),
    }
    
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
    
    def get_location(self, district: str) -> Tuple[float, float]:
        """
        Get latitude and longitude for a district.
        Returns a default location if district not found.
        """
        district_lower = district.lower()
        if district_lower in self.DISTRICT_LOCATIONS:
            return self.DISTRICT_LOCATIONS[district_lower]
        # Default to Lusaka if not found
        return (-15.3875, 28.3228)
    
    def parse(self, text: str, phone: str) -> Optional[ParsedCommand]:
        """Parse raw SMS text into a command."""
        text = text.strip().upper()
        
        # Detect language
        language = self._detect_language(text)
        
        # Extract the command (first word)
        words = text.split()
        if not words:
            return None
        
        try:
            command = Command(words[0])
        except ValueError:
            return None
        
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
        Returns: [produce, quantity, unit, price, district]
        """
        if len(words) < 5:
            return None
        
        produce = words[1]
        
        quantity_match = re.match(r'(\d+)(kg|ton|bundle)?', words[2])
        if not quantity_match:
            return None
        
        quantity = quantity_match.group(1)
        unit = quantity_match.group(2) or "kg"
        
        price = words[3]
        if price.startswith('K'):
            price = price[1:]
        
        district = ' '.join(words[4:])
        
        return [produce, quantity, unit, price, district]
    
    def _parse_list(self, text: str, words: List[str]) -> Optional[List[str]]:
        """Parse LIST command."""
        args = []
        if len(words) > 1:
            args.append(words[1])
        if len(words) > 2:
            args.append(' '.join(words[2:]))
        return args
    
    def _parse_bid(self, text: str, words: List[str]) -> Optional[List[str]]:
        """Parse BID command."""
        if len(words) < 3:
            return None
        
        listing_id = words[1]
        amount = words[2]
        if amount.startswith('K'):
            amount = amount[1:]
        
        return [listing_id, amount]
    
    def _parse_accept(self, text: str, words: List[str]) -> Optional[List[str]]:
        """Parse ACCEPT command."""
        if len(words) < 2:
            return None
        return [words[1]]
    
    def _parse_pay(self, text: str, words: List[str]) -> Optional[List[str]]:
        """Parse PAY command."""
        if len(words) < 2:
            return None
        return [words[1]]
    
    def _parse_confirm(self, text: str, words: List[str]) -> Optional[List[str]]:
        """Parse CONFIRM command."""
        if len(words) < 2:
            return None
        return [words[1]]
    
    def _parse_rate(self, text: str, words: List[str]) -> Optional[List[str]]:
        """Parse RATE command."""
        if len(words) < 3:
            return None
        user_id = words[1]
        score = words[2]
        comment = ' '.join(words[3:]) if len(words) > 3 else ''
        return [user_id, score, comment]
    
    def _parse_price(self, text: str, words: List[str]) -> Optional[List[str]]:
        """Parse PRICE command."""
        if len(words) < 2:
            return None
        produce = words[1]
        district = ' '.join(words[2:]) if len(words) > 2 else ''
        return [produce, district]
    
    def _parse_help(self, text: str, words: List[str]) -> Optional[List[str]]:
        return []
    
    def _parse_status(self, text: str, words: List[str]) -> Optional[List[str]]:
        return words[1:] if len(words) > 1 else []
    
    def _detect_language(self, text: str) -> Language:
        """Detect language from SMS text."""
        # Simple detection - look for keywords in local languages
        text_lower = text.lower()
        bemba_keywords = ['mwashibukeni', 'mwabonwa', 'ulebemba']
        nyanja_keywords = ['muli bwanji', 'zili bwanji', 'ndiyamika']
        tonga_keywords = ['mwabuka buti', 'mwabonwa', 'zili buti']
        lozi_keywords = ['mwabuka buti', 'zili buti', 'ndiyamika']
        
        for word in bemba_keywords:
            if word in text_lower:
                return Language.BEMBA
        for word in nyanja_keywords:
            if word in text_lower:
                return Language.NYANJA
        for word in tonga_keywords:
            if word in text_lower:
                return Language.TONGA
        for word in lozi_keywords:
            if word in text_lower:
                return Language.LOZI
        
        return Language.ENGLISH


# Create a singleton instance
command_parser = CommandParser()
