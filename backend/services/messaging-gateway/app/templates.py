"""
SMS Templates for AgriConnect.

Local language support for Nyanja, Bemba, Tonga, and Lozi.
"""
from typing import Dict, Optional
from app.models import Language


class SMSTemplates:
    """
    SMS templates in multiple languages.
    
    Each template has a key and translations in different languages.
    """
    
    TEMPLATES: Dict[str, Dict[str, str]] = {
        # ====================================================================
        # WELCOME
        # ====================================================================
        "welcome": {
            "en": "Welcome to AgriConnect! 🌾 Reply HELP for commands.",
            "ny": "Takulandilani ku AgriConnect! 🌾 Yankhani HELP kuti mudziwe zambiri.",
            "bem": "Mwabonwa ku AgriConnect! 🌾 Lembani HELP kuti mumbe.",
            "toi": "Mwabuka bantu ku AgriConnect! 🌾 Lembani HELP.",
            "loz": "Mwabuka bantu ku AgriConnect! 🌾 Lembani HELP."
        },
        
        # ====================================================================
        # REGISTRATION
        # ====================================================================
        "register_prompt": {
            "en": "To register, reply: REGISTER <your_name>",
            "ny": "Kulembetsa, yankhani: REGISTER <dzina_wanu>",
            "bem": "Ukulemba, lembani: REGISTER <ishina_lyenu>",
            "toi": "Kujanjiswa, lembani: REGISTER <zina_lyanu>",
            "loz": "Kujanjiswa, lembani: REGISTER <libizo_lyenu>"
        },
        
        # ====================================================================
        # SELL COMMAND
        # ====================================================================
        "sell_success": {
            "en": "✅ Listing created! ID: {listing_id}. Your {produce} ({quantity}{unit}) is listed at K{price} in {district}.",
            "ny": "✅ Zaulitsidwa! ID: {listing_id}. {produce} yanu ({quantity}{unit}) yagulitsidwa pa K{price} ku {district}.",
            "bem": "✅ Yalembwa! ID: {listing_id}. {produce} yenu ({quantity}{unit}) yalembwa pa K{price} mu {district}.",
            "toi": "✅ Yalembwa! ID: {listing_id}. {produce} yanu ({quantity}{unit}) yalembwa pa K{price} mu {district}.",
            "loz": "✅ Yalembwa! ID: {listing_id}. {produce} yanu ({quantity}{unit}) yalembwa pa K{price} mu {district}."
        },
        
        "sell_error": {
            "en": "❌ Invalid SELL format. Use: SELL <produce> <quantity> <price> <district>",
            "ny": "❌ SELL yalephera. Gwiritsani: SELL <chakudya> <kuchuluka> <mtengo> <boma>",
            "bem": "❌ SELL yalepwa. Lembani: SELL <ifya> <inji> <malilo> <distriki>",
            "toi": "❌ SELL yalepwa. Lembani: SELL <zilimwa> <kuchuluka> <malilo> <distriki>",
            "loz": "❌ SELL yalepwa. Lembani: SELL <zilimwa> <kuchuluka> <malilo> <distriki>"
        },
        
        # ====================================================================
        # BID COMMAND
        # ====================================================================
        "bid_success": {
            "en": "✅ Bid placed! You offered K{amount} for listing {listing_id}.",
            "ny": "✅ Bidi yaikidwa! Mwapereka K{amount} pa listing {listing_id}.",
            "bem": "✅ Bid yalembwa! Mwapele K{amount} pa listing {listing_id}.",
            "toi": "✅ Bid yalembwa! Mwapele K{amount} pa listing {listing_id}.",
            "loz": "✅ Bid yalembwa! Mwapele K{amount} pa listing {listing_id}."
        },
        
        "bid_notification": {
            "en": "🔔 New bid! {buyer} offered K{amount} for your listing {listing_id}. Reply ACCEPT {bid_id} to accept.",
            "ny": "🔔 Bidi yatsopano! {buyer} wapereka K{amount} pa listing yanu {listing_id}. Yankhani ACCEPT {bid_id}.",
            "bem": "🔔 Bid iyabwa! {buyer} apele K{amount} pa listing yenu {listing_id}. Lembani ACCEPT {bid_id}.",
            "toi": "🔔 Bid iyabwa! {buyer} apele K{amount} pa listing yanu {listing_id}. Lembani ACCEPT {bid_id}.",
            "loz": "🔔 Bid iyabwa! {buyer} apele K{amount} pa listing yanu {listing_id}. Lembani ACCEPT {bid_id}."
        },
        
        # ====================================================================
        # HELP COMMAND
        # ====================================================================
        "help": {
            "en": "📖 Commands: SELL <produce> <qty> <price> <district> | LIST <produce> <district> | BID <id> <amount> | ACCEPT <id> | PAY <id> | CONFIRM <id> | RATE <id> <score> | PRICE <produce> <district> | STATUS <id>",
            "ny": "📖 Malamulo: SELL <chakudya> <kuchuluka> <mtengo> <boma> | LIST <chakudya> <boma> | BID <id> <ndalama> | ACCEPT <id> | PAY <id> | CONFIRM <id> | RATE <id> <malingaliro> | PRICE <chakudya> <boma> | STATUS <id>",
            "bem": "📖 Malamulo: SELL <ifya> <inji> <malilo> <distriki> | LIST <ifya> <distriki> | BID <id> <indalama> | ACCEPT <id> | PAY <id> | CONFIRM <id> | RATE <id> <malingaliro> | PRICE <ifya> <distriki> | STATUS <id>",
            "toi": "📖 Malamulo: SELL <zilimwa> <kuchuluka> <malilo> <distriki> | LIST <zilimwa> <distriki> | BID <id> <indalama> | ACCEPT <id> | PAY <id> | CONFIRM <id> | RATE <id> <malingaliro> | PRICE <zilimwa> <distriki> | STATUS <id>",
            "loz": "📖 Malamulo: SELL <zilimwa> <kuchuluka> <malilo> <distriki> | LIST <zilimwa> <distriki> | BID <id> <indalama> | ACCEPT <id> | PAY <id> | CONFIRM <id> | RATE <id> <malingaliro> | PRICE <zilimwa> <distriki> | STATUS <id>"
        }
    }
    
    @classmethod
    def get(cls, key: str, language: Language = Language.ENGLISH, **kwargs) -> str:
        """
        Get a template in the specified language.
        
        Args:
            key: Template key (e.g., "welcome", "sell_success")
            language: Language to use
            **kwargs: Variables to substitute in the template
        
        Returns:
            Formatted template string
        """
        # Get the language dictionary
        lang_dict = cls.TEMPLATES.get(key, {})
        
        # Get the template in the requested language, fallback to English
        template = lang_dict.get(language.value, lang_dict.get("en", ""))
        
        # Substitute variables
        if kwargs:
            try:
                template = template.format(**kwargs)
            except KeyError:
                # If a variable is missing, return the raw template
                pass
        
        return template
    
    @classmethod
    def get_all_languages(cls, key: str) -> Dict[str, str]:
        """Get a template in all languages."""
        return cls.TEMPLATES.get(key, {})
