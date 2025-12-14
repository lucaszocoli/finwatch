from typing import Optional, Tuple
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
import redis
import json
from decimal import Decimal

from app.core.logging_config import get_logger

logger = get_logger("geocoding")


class GeocodingService:
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self.geolocator = Nominatim(
            user_agent="finwatch/1.0",
            timeout=10
        )
        self.redis_client = redis_client
        self.cache_ttl = 86400 * 30
    
    def geocode_address(
        self,
        city: str,
        state: Optional[str] = None,
        country: str = "Brazil"
    ) -> Tuple[Optional[Decimal], Optional[Decimal]]:
        
        cache_key = f"geocode:{city}:{state}:{country}"
        
        if self.redis_client:
            try:
                cached = self.redis_client.get(cache_key)
                if cached:
                    data = json.loads(cached)
                    logger.debug(f"Geocoding cache hit for {city}, {state}, {country}")
                    return (
                        Decimal(str(data['lat'])) if data['lat'] else None,
                        Decimal(str(data['lon'])) if data['lon'] else None
                    )
            except Exception as e:
                logger.warning(f"Redis cache read error: {e}")
        
        try:
            address_parts = [city]
            if state:
                address_parts.append(state)
            address_parts.append(country)
            
            address = ", ".join(address_parts)
            
            logger.info(f"Geocoding address: {address}")
            location = self.geolocator.geocode(address)
            
            if location:
                lat = Decimal(str(location.latitude))
                lon = Decimal(str(location.longitude))
                
                logger.info(
                    f"Geocoding successful - {address}: "
                    f"({lat}, {lon})"
                )
                
                if self.redis_client:
                    try:
                        cache_data = json.dumps({
                            'lat': float(lat),
                            'lon': float(lon),
                            'address': address
                        })
                        self.redis_client.setex(cache_key, self.cache_ttl, cache_data)
                        logger.debug(f"Cached geocoding result for {address}")
                    except Exception as e:
                        logger.warning(f"Redis cache write error: {e}")
                
                return lat, lon
            else:
                logger.warning(f"Geocoding returned no results for: {address}")
                return None, None
                
        except GeocoderTimedOut:
            logger.error(f"Geocoding timeout for: {city}, {state}, {country}")
            return None, None
        except GeocoderServiceError as e:
            logger.error(f"Geocoding service error: {e}")
            return None, None
        except Exception as e:
            logger.error(f"Unexpected geocoding error: {e}")
            return None, None
    
    def reverse_geocode(
        self,
        latitude: Decimal,
        longitude: Decimal
    ) -> Optional[dict]:
        
        cache_key = f"reverse_geocode:{latitude}:{longitude}"
        
        if self.redis_client:
            try:
                cached = self.redis_client.get(cache_key)
                if cached:
                    logger.debug(f"Reverse geocoding cache hit for ({latitude}, {longitude})")
                    return json.loads(cached)
            except Exception as e:
                logger.warning(f"Redis cache read error: {e}")
        
        try:
            logger.info(f"Reverse geocoding: ({latitude}, {longitude})")
            location = self.geolocator.reverse(f"{latitude}, {longitude}")
            
            if location and location.raw.get('address'):
                address = location.raw['address']
                result = {
                    'city': address.get('city') or address.get('town') or address.get('village'),
                    'state': address.get('state'),
                    'country': address.get('country'),
                    'formatted': location.address
                }
                
                logger.info(f"Reverse geocoding successful: {result.get('formatted')}")
                
                if self.redis_client:
                    try:
                        self.redis_client.setex(
                            cache_key,
                            self.cache_ttl,
                            json.dumps(result)
                        )
                    except Exception as e:
                        logger.warning(f"Redis cache write error: {e}")
                
                return result
            else:
                logger.warning(f"Reverse geocoding returned no results for: ({latitude}, {longitude})")
                return None
                
        except GeocoderTimedOut:
            logger.error(f"Reverse geocoding timeout for: ({latitude}, {longitude})")
            return None
        except GeocoderServiceError as e:
            logger.error(f"Reverse geocoding service error: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected reverse geocoding error: {e}")
            return None
