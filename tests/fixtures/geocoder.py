from typing import Callable

import pytest

from ma_saas.constants.company import CUR


@pytest.fixture
def search_by_non_format_field_data_fi_(get_cu_fi):
    geocoder_response = {
        "response": {
            "GeoObjectCollection": {
                "metaDataProperty": {
                    "GeocoderResponseMetaData": {
                        "boundedBy": {
                            "Envelope": {
                                "lowerCorner": "-0.250001 -0.250003",
                                "upperCorner": "0.250001 0.250003",
                            }
                        },
                        "request": "('проспект мира, дом 1',)",
                        "results": "10",
                        "found": "10",
                    }
                },
                "featureMember": [
                    {
                        "GeoObject": {
                            "metaDataProperty": {
                                "GeocoderMetaData": {
                                    "precision": "exact",
                                    "text": "Россия, Москва, проспект Мира, 1",
                                    "kind": "house",
                                    "Address": {
                                        "country_code": "RU",
                                        "formatted": "Россия, Москва, проспект Мира, 1",
                                        "postal_code": "129090",
                                        "Components": [
                                            {"kind": "country", "name": "Россия"},
                                            {"kind": "province", "name": "Центральный федеральный округ"},
                                            {"kind": "province", "name": "Москва"},
                                            {"kind": "locality", "name": "Москва"},
                                            {"kind": "street", "name": "проспект Мира"},
                                            {"kind": "house", "name": "1"},
                                        ],
                                    },
                                    "AddressDetails": {
                                        "Country": {
                                            "AddressLine": "Россия, Москва, проспект Мира, 1",
                                            "CountryNameCode": "RU",
                                            "CountryName": "Россия",
                                            "AdministrativeArea": {
                                                "AdministrativeAreaName": "Москва",
                                                "Locality": {
                                                    "LocalityName": "Москва",
                                                    "Thoroughfare": {
                                                        "ThoroughfareName": "проспект Мира",
                                                        "Premise": {
                                                            "PremiseNumber": "1",
                                                            "PostalCode": {"PostalCodeNumber": "129090"},
                                                        },
                                                    },
                                                },
                                            },
                                        }
                                    },
                                }
                            },
                            "name": "проспект Мира, 1",
                            "description": "Москва, Россия",
                            "boundedBy": {
                                "Envelope": {
                                    "lowerCorner": "37.627616 55.770816",
                                    "upperCorner": "37.635826 55.775444",
                                }
                            },
                            "Point": {"pos": "37.631721 55.77313"},
                        }
                    },
                    {
                        "GeoObject": {
                            "metaDataProperty": {
                                "GeocoderMetaData": {
                                    "precision": "exact",
                                    "text": "Беларусь, Могилёв, проспект Мира, 1",
                                    "kind": "house",
                                    "Address": {
                                        "country_code": "BY",
                                        "formatted": "Беларусь, Могилёв, проспект Мира, 1",
                                        "Components": [
                                            {"kind": "country", "name": "Беларусь"},
                                            {"kind": "province", "name": "Могилёвская область"},
                                            {"kind": "locality", "name": "Могилёв"},
                                            {"kind": "street", "name": "проспект Мира"},
                                            {"kind": "house", "name": "1"},
                                        ],
                                    },
                                    "AddressDetails": {
                                        "Country": {
                                            "AddressLine": "Беларусь, Могилёв, проспект Мира, 1",
                                            "CountryNameCode": "BY",
                                            "CountryName": "Беларусь",
                                            "AdministrativeArea": {
                                                "AdministrativeAreaName": "Могилёвская область",
                                                "Locality": {
                                                    "LocalityName": "Могилёв",
                                                    "Thoroughfare": {
                                                        "ThoroughfareName": "проспект Мира",
                                                        "Premise": {"PremiseNumber": "1"},
                                                    },
                                                },
                                            },
                                        }
                                    },
                                }
                            },
                            "name": "проспект Мира, 1",
                            "description": "Могилёв, Беларусь",
                            "boundedBy": {
                                "Envelope": {
                                    "lowerCorner": "30.315769 53.909683",
                                    "upperCorner": "30.32398 53.914531",
                                }
                            },
                            "Point": {"pos": "30.319875 53.912107"},
                        }
                    },
                    {
                        "GeoObject": {
                            "metaDataProperty": {
                                "GeocoderMetaData": {
                                    "precision": "exact",
                                    "text": "Беларусь, Минск, проспект Мира, 1",
                                    "kind": "house",
                                    "Address": {
                                        "country_code": "BY",
                                        "formatted": "Беларусь, Минск, проспект Мира, 1",
                                        "Components": [
                                            {"kind": "country", "name": "Беларусь"},
                                            {"kind": "province", "name": "Минск"},
                                            {"kind": "locality", "name": "Минск"},
                                            {"kind": "street", "name": "проспект Мира"},
                                            {"kind": "house", "name": "1"},
                                        ],
                                    },
                                    "AddressDetails": {
                                        "Country": {
                                            "AddressLine": "Беларусь, Минск, проспект Мира, 1",
                                            "CountryNameCode": "BY",
                                            "CountryName": "Беларусь",
                                            "AdministrativeArea": {
                                                "AdministrativeAreaName": "Минск",
                                                "Locality": {
                                                    "LocalityName": "Минск",
                                                    "Thoroughfare": {
                                                        "ThoroughfareName": "проспект Мира",
                                                        "Premise": {"PremiseNumber": "1"},
                                                    },
                                                },
                                            },
                                        }
                                    },
                                }
                            },
                            "name": "проспект Мира, 1",
                            "description": "Минск, Беларусь",
                            "boundedBy": {
                                "Envelope": {
                                    "lowerCorner": "27.545832 53.867586",
                                    "upperCorner": "27.554043 53.872438",
                                }
                            },
                            "Point": {"pos": "27.549937 53.870012"},
                        }
                    },
                    {
                        "GeoObject": {
                            "metaDataProperty": {
                                "GeocoderMetaData": {
                                    "precision": "exact",
                                    "text": "Россия, Омск, проспект Мира, 1",
                                    "kind": "house",
                                    "Address": {
                                        "country_code": "RU",
                                        "formatted": "Россия, Омск, проспект Мира, 1",
                                        "postal_code": "644008",
                                        "Components": [
                                            {"kind": "country", "name": "Россия"},
                                            {"kind": "province", "name": "Сибирский федеральный округ"},
                                            {"kind": "province", "name": "Омская область"},
                                            {"kind": "area", "name": "городской округ Омск"},
                                            {"kind": "locality", "name": "Омск"},
                                            {"kind": "street", "name": "проспект Мира"},
                                            {"kind": "house", "name": "1"},
                                        ],
                                    },
                                    "AddressDetails": {
                                        "Country": {
                                            "AddressLine": "Россия, Омск, проспект Мира, 1",
                                            "CountryNameCode": "RU",
                                            "CountryName": "Россия",
                                            "AdministrativeArea": {
                                                "AdministrativeAreaName": "Омская область",
                                                "SubAdministrativeArea": {
                                                    "SubAdministrativeAreaName": "городской округ Омск",
                                                    "Locality": {
                                                        "LocalityName": "Омск",
                                                        "Thoroughfare": {
                                                            "ThoroughfareName": "проспект Мира",
                                                            "Premise": {
                                                                "PremiseNumber": "1",
                                                                "PostalCode": {"PostalCodeNumber": "644008"},
                                                            },
                                                        },
                                                    },
                                                },
                                            },
                                        }
                                    },
                                }
                            },
                            "name": "проспект Мира, 1",
                            "description": "Омск, Россия",
                            "boundedBy": {
                                "Envelope": {
                                    "lowerCorner": "73.301916 55.018582",
                                    "upperCorner": "73.310127 55.0233",
                                }
                            },
                            "Point": {"pos": "73.306022 55.020941"},
                        }
                    },
                    {
                        "GeoObject": {
                            "metaDataProperty": {
                                "GeocoderMetaData": {
                                    "precision": "exact",
                                    "text": "Абхазия, Сухум, проспект Аиааира, 1",
                                    "kind": "house",
                                    "Address": {
                                        "country_code": "AB",
                                        "formatted": "Абхазия, Сухум, проспект Аиааира, 1",
                                        "Components": [
                                            {"kind": "country", "name": "Абхазия"},
                                            {"kind": "locality", "name": "Сухум"},
                                            {"kind": "street", "name": "проспект Аиааира"},
                                            {"kind": "house", "name": "1"},
                                        ],
                                    },
                                    "AddressDetails": {
                                        "Country": {
                                            "AddressLine": "Абхазия, Сухум, проспект Аиааира, 1",
                                            "CountryNameCode": "AB",
                                            "CountryName": "Абхазия",
                                            "Locality": {
                                                "LocalityName": "Сухум",
                                                "Thoroughfare": {
                                                    "ThoroughfareName": "проспект Аиааира",
                                                    "Premise": {"PremiseNumber": "1"},
                                                },
                                            },
                                        }
                                    },
                                }
                            },
                            "name": "проспект Аиааира, 1",
                            "description": "Сухум, Абхазия",
                            "boundedBy": {
                                "Envelope": {
                                    "lowerCorner": "41.02817 42.999981",
                                    "upperCorner": "41.036381 43.006008",
                                }
                            },
                            "Point": {"pos": "41.032275 43.002995"},
                        }
                    },
                    {
                        "GeoObject": {
                            "metaDataProperty": {
                                "GeocoderMetaData": {
                                    "precision": "exact",
                                    "text": "Украина, Донецк, проспект Мира, 1",
                                    "kind": "house",
                                    "Address": {
                                        "country_code": "UA",
                                        "formatted": "Украина, Донецк, проспект Мира, 1",
                                        "Components": [
                                            {"kind": "country", "name": "Украина"},
                                            {"kind": "province", "name": "Донецкая область"},
                                            {"kind": "area", "name": "Донецкий городской совет"},
                                            {"kind": "locality", "name": "Донецк"},
                                            {"kind": "street", "name": "проспект Мира"},
                                            {"kind": "house", "name": "1"},
                                        ],
                                    },
                                    "AddressDetails": {
                                        "Country": {
                                            "AddressLine": "Украина, Донецк, проспект Мира, 1",
                                            "CountryNameCode": "UA",
                                            "CountryName": "Украина",
                                            "AdministrativeArea": {
                                                "AdministrativeAreaName": "Донецкая область",
                                                "SubAdministrativeArea": {
                                                    "SubAdministrativeAreaName": "Донецкий городской совет",
                                                    "Locality": {
                                                        "LocalityName": "Донецк",
                                                        "Thoroughfare": {
                                                            "ThoroughfareName": "проспект Мира",
                                                            "Premise": {"PremiseNumber": "1"},
                                                        },
                                                    },
                                                },
                                            },
                                        }
                                    },
                                }
                            },
                            "name": "проспект Мира, 1",
                            "description": "Донецк, Украина",
                            "boundedBy": {
                                "Envelope": {
                                    "lowerCorner": "37.782746 48.013907",
                                    "upperCorner": "37.790956 48.019415",
                                }
                            },
                            "Point": {"pos": "37.786851 48.016661"},
                        }
                    },
                    {
                        "GeoObject": {
                            "metaDataProperty": {
                                "GeocoderMetaData": {
                                    "precision": "exact",
                                    "text": "Россия, Калининград, проспект Мира, 1",
                                    "kind": "house",
                                    "Address": {
                                        "country_code": "RU",
                                        "formatted": "Россия, Калининград, проспект Мира, 1",
                                        "postal_code": "236022",
                                        "Components": [
                                            {"kind": "country", "name": "Россия"},
                                            {"kind": "province", "name": "Северо-Западный федеральный округ"},
                                            {"kind": "province", "name": "Калининградская область"},
                                            {"kind": "area", "name": "городской округ Калининград"},
                                            {"kind": "locality", "name": "Калининград"},
                                            {"kind": "street", "name": "проспект Мира"},
                                            {"kind": "house", "name": "1"},
                                        ],
                                    },
                                    "AddressDetails": {
                                        "Country": {
                                            "AddressLine": "Россия, Калининград, проспект Мира, 1",
                                            "CountryNameCode": "RU",
                                            "CountryName": "Россия",
                                            "AdministrativeArea": {
                                                "AdministrativeAreaName": "Калининградская область",
                                                "SubAdministrativeArea": {
                                                    "SubAdministrativeAreaName": "городской округ Калининград",
                                                    "Locality": {
                                                        "LocalityName": "Калининград",
                                                        "Thoroughfare": {
                                                            "ThoroughfareName": "проспект Мира",
                                                            "Premise": {
                                                                "PremiseNumber": "1",
                                                                "PostalCode": {"PostalCodeNumber": "236022"},
                                                            },
                                                        },
                                                    },
                                                },
                                            },
                                        }
                                    },
                                }
                            },
                            "name": "проспект Мира, 1",
                            "description": "Калининград, Россия",
                            "boundedBy": {
                                "Envelope": {
                                    "lowerCorner": "20.493563 54.717157",
                                    "upperCorner": "20.501774 54.72191",
                                }
                            },
                            "Point": {"pos": "20.497668 54.719534"},
                        }
                    },
                    {
                        "GeoObject": {
                            "metaDataProperty": {
                                "GeocoderMetaData": {
                                    "precision": "exact",
                                    "text": "Россия, Красноярск, проспект Мира, 1",
                                    "kind": "house",
                                    "Address": {
                                        "country_code": "RU",
                                        "formatted": "Россия, Красноярск, проспект Мира, 1",
                                        "Components": [
                                            {"kind": "country", "name": "Россия"},
                                            {"kind": "province", "name": "Сибирский федеральный округ"},
                                            {"kind": "province", "name": "Красноярский край"},
                                            {"kind": "area", "name": "городской округ Красноярск"},
                                            {"kind": "locality", "name": "Красноярск"},
                                            {"kind": "street", "name": "проспект Мира"},
                                            {"kind": "house", "name": "1"},
                                        ],
                                    },
                                    "AddressDetails": {
                                        "Country": {
                                            "AddressLine": "Россия, Красноярск, проспект Мира, 1",
                                            "CountryNameCode": "RU",
                                            "CountryName": "Россия",
                                            "AdministrativeArea": {
                                                "AdministrativeAreaName": "Красноярский край",
                                                "SubAdministrativeArea": {
                                                    "SubAdministrativeAreaName": "городской округ Красноярск",
                                                    "Locality": {
                                                        "LocalityName": "Красноярск",
                                                        "Thoroughfare": {
                                                            "ThoroughfareName": "проспект Мира",
                                                            "Premise": {"PremiseNumber": "1"},
                                                        },
                                                    },
                                                },
                                            },
                                        }
                                    },
                                }
                            },
                            "name": "проспект Мира, 1",
                            "description": "Красноярск, Россия",
                            "boundedBy": {
                                "Envelope": {
                                    "lowerCorner": "92.889609 56.008555",
                                    "upperCorner": "92.89782 56.013155",
                                }
                            },
                            "Point": {"pos": "92.893715 56.010855"},
                        }
                    },
                    {
                        "GeoObject": {
                            "metaDataProperty": {
                                "GeocoderMetaData": {
                                    "precision": "exact",
                                    "text": "Россия, Томск, проспект Мира, 1",
                                    "kind": "house",
                                    "Address": {
                                        "country_code": "RU",
                                        "formatted": "Россия, Томск, проспект Мира, 1",
                                        "postal_code": "634057",
                                        "Components": [
                                            {"kind": "country", "name": "Россия"},
                                            {"kind": "province", "name": "Сибирский федеральный округ"},
                                            {"kind": "province", "name": "Томская область"},
                                            {"kind": "area", "name": "городской округ Томск"},
                                            {"kind": "locality", "name": "Томск"},
                                            {"kind": "street", "name": "проспект Мира"},
                                            {"kind": "house", "name": "1"},
                                        ],
                                    },
                                    "AddressDetails": {
                                        "Country": {
                                            "AddressLine": "Россия, Томск, проспект Мира, 1",
                                            "CountryNameCode": "RU",
                                            "CountryName": "Россия",
                                            "AdministrativeArea": {
                                                "AdministrativeAreaName": "Томская область",
                                                "SubAdministrativeArea": {
                                                    "SubAdministrativeAreaName": "городской округ Томск",
                                                    "Locality": {
                                                        "LocalityName": "Томск",
                                                        "Thoroughfare": {
                                                            "ThoroughfareName": "проспект Мира",
                                                            "Premise": {
                                                                "PremiseNumber": "1",
                                                                "PostalCode": {"PostalCodeNumber": "634057"},
                                                            },
                                                        },
                                                    },
                                                },
                                            },
                                        }
                                    },
                                }
                            },
                            "name": "проспект Мира, 1",
                            "description": "Томск, Россия",
                            "boundedBy": {
                                "Envelope": {
                                    "lowerCorner": "84.965741 56.506876",
                                    "upperCorner": "84.973951 56.511416",
                                }
                            },
                            "Point": {"pos": "84.969846 56.509146"},
                        }
                    },
                ],
            }
        }
    }

    return (
        "проспект Мира, дом 1",
        geocoder_response,
        [
            {
                "city": "Москва",
                "formatted": "проспект Мира, 1",
                "description": "Москва, Россия",
                "lat": 55.77313,
                "lon": 37.631721,
            },
            {
                "city": "Могилёв",
                "formatted": "проспект Мира, 1",
                "description": "Могилёв, Беларусь",
                "lat": 53.912107,
                "lon": 30.319875,
            },
            {
                "city": "Минск",
                "formatted": "проспект Мира, 1",
                "description": "Минск, Беларусь",
                "lat": 53.870012,
                "lon": 27.549937,
            },
            {
                "city": "Омск",
                "formatted": "проспект Мира, 1",
                "description": "Омск, Россия",
                "lat": 55.020941,
                "lon": 73.306022,
            },
            {
                "city": "Сухум",
                "formatted": "проспект Аиааира, 1",
                "description": "Сухум, Абхазия",
                "lat": 43.002995,
                "lon": 41.032275,
            },
            {
                "city": "Донецк",
                "formatted": "проспект Мира, 1",
                "description": "Донецк, Украина",
                "lat": 48.016661,
                "lon": 37.786851,
            },
            {
                "city": "Калининград",
                "formatted": "проспект Мира, 1",
                "description": "Калининград, Россия",
                "lat": 54.719534,
                "lon": 20.497668,
            },
            {
                "city": "Красноярск",
                "formatted": "проспект Мира, 1",
                "description": "Красноярск, Россия",
                "lat": 56.010855,
                "lon": 92.893715,
            },
            {
                "city": "Томск",
                "formatted": "проспект Мира, 1",
                "description": "Томск, Россия",
                "lat": 56.509146,
                "lon": 84.969846,
            },
        ],
    )


@pytest.fixture
def search_by_coords_data_fi_(get_cu_fi):
    geocoder_response = {
        "response": {
            "GeoObjectCollection": {
                "metaDataProperty": {
                    "GeocoderResponseMetaData": {
                        "Point": {"pos": "37.839896 55.822124"},
                        "boundedBy": {
                            "Envelope": {
                                "lowerCorner": "37.589895 55.571322",
                                "upperCorner": "38.089898 56.071313",
                            }
                        },
                        "request": "37.839896,55.822124",
                        "results": "10",
                        "found": "10",
                    }
                },
                "featureMember": [
                    {
                        "GeoObject": {
                            "metaDataProperty": {
                                "GeocoderMetaData": {
                                    "precision": "other",
                                    "text": "Россия, Московская область, Балашиха",
                                    "kind": "locality",
                                    "Address": {
                                        "country_code": "RU",
                                        "formatted": "Россия, Московская область, Балашиха",
                                        "Components": [
                                            {"kind": "country", "name": "Россия"},
                                            {"kind": "province", "name": "Центральный федеральный округ"},
                                            {"kind": "province", "name": "Московская область"},
                                            {"kind": "area", "name": "городской округ Балашиха"},
                                            {"kind": "locality", "name": "Балашиха"},
                                        ],
                                    },
                                    "AddressDetails": {
                                        "Country": {
                                            "AddressLine": "Россия, Московская область, Балашиха",
                                            "CountryNameCode": "RU",
                                            "CountryName": "Россия",
                                            "AdministrativeArea": {
                                                "AdministrativeAreaName": "Московская область",
                                                "SubAdministrativeArea": {
                                                    "SubAdministrativeAreaName": "городской округ Балашиха",
                                                    "Locality": {"LocalityName": "Балашиха"},
                                                },
                                            },
                                        }
                                    },
                                }
                            },
                            "name": "Балашиха",
                            "description": "Московская область, Россия",
                            "boundedBy": {
                                "Envelope": {
                                    "lowerCorner": "37.822298 55.705087",
                                    "upperCorner": "38.144731 55.861828",
                                }
                            },
                            "Point": {"pos": "37.938208 55.796344"},
                        }
                    },
                    {
                        "GeoObject": {
                            "metaDataProperty": {
                                "GeocoderMetaData": {
                                    "precision": "other",
                                    "text": "Россия, Московская область, Балашиха",
                                    "kind": "locality",
                                    "Address": {
                                        "country_code": "RU",
                                        "formatted": "Россия, Московская область, Балашиха",
                                        "Components": [
                                            {"kind": "country", "name": "Россия"},
                                            {"kind": "province", "name": "Центральный федеральный округ"},
                                            {"kind": "province", "name": "Московская область"},
                                            {"kind": "area", "name": "городской округ Балашиха"},
                                            {"kind": "locality", "name": "Балашиха"},
                                        ],
                                    },
                                    "AddressDetails": {
                                        "Country": {
                                            "AddressLine": "Россия, Московская область, Балашиха",
                                            "CountryNameCode": "RU",
                                            "CountryName": "Россия",
                                            "AdministrativeArea": {
                                                "AdministrativeAreaName": "Московская область",
                                                "SubAdministrativeArea": {
                                                    "SubAdministrativeAreaName": "городской округ Балашиха",
                                                    "Locality": {"LocalityName": "Балашиха"},
                                                },
                                            },
                                        }
                                    },
                                }
                            },
                            "name": "Балашиха",
                            "description": "Московская область, Россия",
                            "boundedBy": {
                                "Envelope": {
                                    "lowerCorner": "37.822298 55.705087",
                                    "upperCorner": "38.144731 55.861828",
                                }
                            },
                            "Point": {"pos": "37.938208 55.796344"},
                        }
                    },
                    {
                        "GeoObject": {
                            "metaDataProperty": {
                                "GeocoderMetaData": {
                                    "precision": "other",
                                    "text": "Россия, Москва",
                                    "kind": "locality",
                                    "Address": {
                                        "country_code": "RU",
                                        "formatted": "Россия, Москва",
                                        "Components": [
                                            {"kind": "country", "name": "Россия"},
                                            {"kind": "province", "name": "Центральный федеральный округ"},
                                            {"kind": "province", "name": "Москва"},
                                            {"kind": "locality", "name": "Москва"},
                                        ],
                                    },
                                    "AddressDetails": {
                                        "Country": {
                                            "AddressLine": "Россия, Москва",
                                            "CountryNameCode": "RU",
                                            "CountryName": "Россия",
                                            "AdministrativeArea": {
                                                "AdministrativeAreaName": "Москва",
                                                "Locality": {"LocalityName": "Москва"},
                                            },
                                        }
                                    },
                                }
                            },
                            "name": "Москва",
                            "description": "Россия",
                            "boundedBy": {
                                "Envelope": {
                                    "lowerCorner": "37.32606 55.49133",
                                    "upperCorner": "37.967799 55.957565",
                                }
                            },
                            "Point": {"pos": "37.617644 55.755819"},
                        }
                    },
                    {
                        "GeoObject": {
                            "metaDataProperty": {
                                "GeocoderMetaData": {
                                    "precision": "other",
                                    "text": "Россия, Москва, посёлок Восточный",
                                    "kind": "locality",
                                    "Address": {
                                        "country_code": "RU",
                                        "formatted": "Россия, Москва, посёлок Восточный",
                                        "Components": [
                                            {"kind": "country", "name": "Россия"},
                                            {"kind": "province", "name": "Центральный федеральный округ"},
                                            {"kind": "province", "name": "Москва"},
                                            {"kind": "locality", "name": "посёлок Восточный"},
                                        ],
                                    },
                                    "AddressDetails": {
                                        "Country": {
                                            "AddressLine": "Россия, Москва, посёлок Восточный",
                                            "CountryNameCode": "RU",
                                            "CountryName": "Россия",
                                            "AdministrativeArea": {
                                                "AdministrativeAreaName": "Москва",
                                                "Locality": {"LocalityName": "посёлок Восточный"},
                                            },
                                        }
                                    },
                                }
                            },
                            "name": "посёлок Восточный",
                            "description": "Москва, Россия",
                            "boundedBy": {
                                "Envelope": {
                                    "lowerCorner": "37.84561 55.804036",
                                    "upperCorner": "37.89976 55.825361",
                                }
                            },
                            "Point": {"pos": "37.867017 55.819171"},
                        }
                    },
                ],
            }
        }
    }
    return (
        37.839896,
        55.822124,
        geocoder_response,
        [
            {
                "city": "Балашиха",
                "formatted": "Балашиха",
                "description": "Московская область, Россия",
                "lat": 55.796344,
                "lon": 37.938208,
            },
            {
                "city": "Москва",
                "formatted": "Москва",
                "description": "Россия",
                "lat": 55.755819,
                "lon": 37.617644,
            },
            {
                "city": "посёлок Восточный",
                "formatted": "посёлок Восточный",
                "description": "Москва, Россия",
                "lat": 55.819171,
                "lon": 37.867017,
            },
        ],
    )


@pytest.fixture
def search_by_city_data_fi_(get_cu_fi):
    geocoder_response = {
        "response": {
            "GeoObjectCollection": {
                "metaDataProperty": {
                    "GeocoderResponseMetaData": {
                        "Point": {"pos": "37.622513 55.75322"},
                        "request": "37.622513,55.75322",
                        "results": "10",
                        "found": "8",
                    }
                },
                "featureMember": [
                    {
                        "GeoObject": {
                            "metaDataProperty": {
                                "GeocoderMetaData": {
                                    "precision": "street",
                                    "text": "Россия, Москва, Красная площадь",
                                    "kind": "street",
                                    "Address": {
                                        "country_code": "RU",
                                        "formatted": "Россия, Москва, Красная площадь",
                                        "Components": [
                                            {"kind": "country", "name": "Россия"},
                                            {"kind": "province", "name": "Центральный федеральный округ"},
                                            {"kind": "province", "name": "Москва"},
                                            {"kind": "locality", "name": "Москва"},
                                            {"kind": "street", "name": "Красная площадь"},
                                        ],
                                    },
                                    "AddressDetails": {
                                        "Country": {
                                            "AddressLine": "Россия, Москва, Красная площадь",
                                            "CountryNameCode": "RU",
                                            "CountryName": "Россия",
                                            "AdministrativeArea": {
                                                "AdministrativeAreaName": "Москва",
                                                "Locality": {
                                                    "LocalityName": "Москва",
                                                    "Thoroughfare": {"ThoroughfareName": "Красная площадь"},
                                                },
                                            },
                                        }
                                    },
                                }
                            },
                            "name": "Красная площадь",
                            "description": "Москва, Россия",
                            "boundedBy": {
                                "Envelope": {
                                    "lowerCorner": "37.617968 55.752029",
                                    "upperCorner": "37.623816 55.755257",
                                }
                            },
                            "Point": {"pos": "37.621094 55.753605"},
                        }
                    },
                    {
                        "GeoObject": {
                            "metaDataProperty": {
                                "GeocoderMetaData": {
                                    "precision": "other",
                                    "text": "Россия, Москва, Центральный административный округ, Тверской район, 16-й квартал",
                                    "kind": "district",
                                    "Address": {
                                        "country_code": "RU",
                                        "formatted": "Россия, Москва, Центральный административный округ, Тверской район, 16-й квартал",
                                        "Components": [
                                            {"kind": "country", "name": "Россия"},
                                            {"kind": "province", "name": "Центральный федеральный округ"},
                                            {"kind": "province", "name": "Москва"},
                                            {"kind": "locality", "name": "Москва"},
                                            {
                                                "kind": "district",
                                                "name": "Центральный административный округ",
                                            },
                                            {"kind": "district", "name": "Тверской район"},
                                            {"kind": "district", "name": "16-й квартал"},
                                        ],
                                    },
                                    "AddressDetails": {
                                        "Country": {
                                            "AddressLine": "Россия, Москва, Центральный административный округ, Тверской район, 16-й квартал",
                                            "CountryNameCode": "RU",
                                            "CountryName": "Россия",
                                            "AdministrativeArea": {
                                                "AdministrativeAreaName": "Москва",
                                                "Locality": {
                                                    "LocalityName": "Москва",
                                                    "DependentLocality": {
                                                        "DependentLocalityName": "Центральный административный округ",
                                                        "DependentLocality": {
                                                            "DependentLocalityName": "Тверской район",
                                                            "DependentLocality": {
                                                                "DependentLocalityName": "16-й квартал"
                                                            },
                                                        },
                                                    },
                                                },
                                            },
                                        }
                                    },
                                }
                            },
                            "name": "16-й квартал",
                            "description": "Тверской район, Центральный административный округ, Москва, Россия",
                            "boundedBy": {
                                "Envelope": {
                                    "lowerCorner": "37.621732 55.752095",
                                    "upperCorner": "37.623888 55.753646",
                                }
                            },
                            "Point": {"pos": "37.622747 55.752951"},
                        }
                    },
                    {
                        "GeoObject": {
                            "metaDataProperty": {
                                "GeocoderMetaData": {
                                    "precision": "other",
                                    "text": "Россия, Москва, Центральный административный округ, Тверской район",
                                    "kind": "district",
                                    "Address": {
                                        "country_code": "RU",
                                        "formatted": "Россия, Москва, Центральный административный округ, Тверской район",
                                        "Components": [
                                            {"kind": "country", "name": "Россия"},
                                            {"kind": "province", "name": "Центральный федеральный округ"},
                                            {"kind": "province", "name": "Москва"},
                                            {"kind": "locality", "name": "Москва"},
                                            {
                                                "kind": "district",
                                                "name": "Центральный административный округ",
                                            },
                                            {"kind": "district", "name": "Тверской район"},
                                        ],
                                    },
                                    "AddressDetails": {
                                        "Country": {
                                            "AddressLine": "Россия, Москва, Центральный административный округ, Тверской район",
                                            "CountryNameCode": "RU",
                                            "CountryName": "Россия",
                                            "AdministrativeArea": {
                                                "AdministrativeAreaName": "Москва",
                                                "Locality": {
                                                    "LocalityName": "Москва",
                                                    "DependentLocality": {
                                                        "DependentLocalityName": "Центральный административный округ",
                                                        "DependentLocality": {
                                                            "DependentLocalityName": "Тверской район"
                                                        },
                                                    },
                                                },
                                            },
                                        }
                                    },
                                }
                            },
                            "name": "Тверской район",
                            "description": "Центральный административный округ, Москва, Россия",
                            "boundedBy": {
                                "Envelope": {
                                    "lowerCorner": "37.575199 55.746841",
                                    "upperCorner": "37.634838 55.792448",
                                }
                            },
                            "Point": {"pos": "37.606918 55.770132"},
                        }
                    },
                    {
                        "GeoObject": {
                            "metaDataProperty": {
                                "GeocoderMetaData": {
                                    "precision": "other",
                                    "text": "Россия, Москва, Центральный административный округ",
                                    "kind": "district",
                                    "Address": {
                                        "country_code": "RU",
                                        "formatted": "Россия, Москва, Центральный административный округ",
                                        "Components": [
                                            {"kind": "country", "name": "Россия"},
                                            {"kind": "province", "name": "Центральный федеральный округ"},
                                            {"kind": "province", "name": "Москва"},
                                            {"kind": "locality", "name": "Москва"},
                                            {
                                                "kind": "district",
                                                "name": "Центральный административный округ",
                                            },
                                        ],
                                    },
                                    "AddressDetails": {
                                        "Country": {
                                            "AddressLine": "Россия, Москва, Центральный административный округ",
                                            "CountryNameCode": "RU",
                                            "CountryName": "Россия",
                                            "AdministrativeArea": {
                                                "AdministrativeAreaName": "Москва",
                                                "Locality": {
                                                    "LocalityName": "Москва",
                                                    "DependentLocality": {
                                                        "DependentLocalityName": "Центральный административный округ"
                                                    },
                                                },
                                            },
                                        }
                                    },
                                }
                            },
                            "name": "Центральный административный округ",
                            "description": "Москва, Россия",
                            "boundedBy": {
                                "Envelope": {
                                    "lowerCorner": "37.51441 55.710276",
                                    "upperCorner": "37.713602 55.797113",
                                }
                            },
                            "Point": {"pos": "37.614069 55.753995"},
                        }
                    },
                    {
                        "GeoObject": {
                            "metaDataProperty": {
                                "GeocoderMetaData": {
                                    "precision": "other",
                                    "text": "Россия, Москва",
                                    "kind": "locality",
                                    "Address": {
                                        "country_code": "RU",
                                        "formatted": "Россия, Москва",
                                        "Components": [
                                            {"kind": "country", "name": "Россия"},
                                            {"kind": "province", "name": "Центральный федеральный округ"},
                                            {"kind": "province", "name": "Москва"},
                                            {"kind": "locality", "name": "Москва"},
                                        ],
                                    },
                                    "AddressDetails": {
                                        "Country": {
                                            "AddressLine": "Россия, Москва",
                                            "CountryNameCode": "RU",
                                            "CountryName": "Россия",
                                            "AdministrativeArea": {
                                                "AdministrativeAreaName": "Москва",
                                                "Locality": {"LocalityName": "Москва"},
                                            },
                                        }
                                    },
                                }
                            },
                            "name": "Москва",
                            "description": "Россия",
                            "boundedBy": {
                                "Envelope": {
                                    "lowerCorner": "37.32606 55.49133",
                                    "upperCorner": "37.967799 55.957565",
                                }
                            },
                            "Point": {"pos": "37.617644 55.755819"},
                        }
                    },
                    {
                        "GeoObject": {
                            "metaDataProperty": {
                                "GeocoderMetaData": {
                                    "precision": "other",
                                    "text": "Россия, Москва",
                                    "kind": "province",
                                    "Address": {
                                        "country_code": "RU",
                                        "formatted": "Россия, Москва",
                                        "Components": [
                                            {"kind": "country", "name": "Россия"},
                                            {"kind": "province", "name": "Центральный федеральный округ"},
                                            {"kind": "province", "name": "Москва"},
                                        ],
                                    },
                                    "AddressDetails": {
                                        "Country": {
                                            "AddressLine": "Россия, Москва",
                                            "CountryNameCode": "RU",
                                            "CountryName": "Россия",
                                            "AdministrativeArea": {"AdministrativeAreaName": "Москва"},
                                        }
                                    },
                                }
                            },
                            "name": "Москва",
                            "description": "Россия",
                            "boundedBy": {
                                "Envelope": {
                                    "lowerCorner": "36.803268 55.142226",
                                    "upperCorner": "37.967799 56.021286",
                                }
                            },
                            "Point": {"pos": "37.622513 55.75322"},
                        }
                    },
                    {
                        "GeoObject": {
                            "metaDataProperty": {
                                "GeocoderMetaData": {
                                    "precision": "other",
                                    "text": "Россия, Центральный федеральный округ",
                                    "kind": "province",
                                    "Address": {
                                        "country_code": "RU",
                                        "formatted": "Россия, Центральный федеральный округ",
                                        "Components": [
                                            {"kind": "country", "name": "Россия"},
                                            {"kind": "province", "name": "Центральный федеральный округ"},
                                        ],
                                    },
                                    "AddressDetails": {
                                        "Country": {
                                            "AddressLine": "Россия, Центральный федеральный округ",
                                            "CountryNameCode": "RU",
                                            "CountryName": "Россия",
                                        }
                                    },
                                }
                            },
                            "name": "Центральный федеральный округ",
                            "description": "Россия",
                            "boundedBy": {
                                "Envelope": {
                                    "lowerCorner": "30.750266 49.556986",
                                    "upperCorner": "47.641729 59.625176",
                                }
                            },
                            "Point": {"pos": "38.064727 54.87375"},
                        }
                    },
                    {
                        "GeoObject": {
                            "metaDataProperty": {
                                "GeocoderMetaData": {
                                    "precision": "other",
                                    "text": "Россия",
                                    "kind": "country",
                                    "Address": {
                                        "country_code": "RU",
                                        "formatted": "Россия",
                                        "Components": [{"kind": "country", "name": "Россия"}],
                                    },
                                    "AddressDetails": {
                                        "Country": {
                                            "AddressLine": "Россия",
                                            "CountryNameCode": "RU",
                                            "CountryName": "Россия",
                                        }
                                    },
                                }
                            },
                            "name": "Россия",
                            "boundedBy": {
                                "Envelope": {
                                    "lowerCorner": "19.484764 41.185996",
                                    "upperCorner": "191.128012 81.886117",
                                }
                            },
                            "Point": {"pos": "99.505405 61.698657"},
                        }
                    },
                ],
            }
        }
    }

    return (
        "Москва",
        geocoder_response,
        # [
        #     {"formatted": "Россия, Москва", "lat": 55.755819, "lon": 37.617644},
        #     {"formatted": "Россия, Москва", "lat": 55.75322, "lon": 37.622513},
        #     {"formatted": "Россия, Центральный федеральный округ", "lat": 54.87375, "lon": 38.064727},
        # ],
        [
            {
                "city": "Москва",
                "formatted": "Москва",
                "description": "Россия",
                "lat": 55.755819,
                "lon": 37.617644,
            },
            {
                "city": "Москва",
                "formatted": "Москва",
                "description": "Россия",
                "lat": 55.75322,
                "lon": 37.622513,
            },
        ],
    )


@pytest.fixture
def search_by_address_data_fi_(get_cu_fi):
    geocoder_response = {
        "response": {
            "GeoObjectCollection": {
                "metaDataProperty": {
                    "GeocoderResponseMetaData": {
                        "boundedBy": {
                            "Envelope": {
                                "lowerCorner": "-0.002497 -0.002496",
                                "upperCorner": "0.002497 0.002496",
                            }
                        },
                        "request": "Москва, Самотечная улица, дом 7, строение 2",
                        "results": "10",
                        "found": "1",
                    }
                },
                "featureMember": [
                    {
                        "GeoObject": {
                            "metaDataProperty": {
                                "GeocoderMetaData": {
                                    "precision": "exact",
                                    "text": "Россия, Москва, Самотёчная улица, 7с2",
                                    "kind": "house",
                                    "Address": {
                                        "country_code": "RU",
                                        "formatted": "Россия, Москва, Самотёчная улица, 7с2",
                                        "postal_code": "127473",
                                        "Components": [
                                            {"kind": "country", "name": "Россия"},
                                            {"kind": "province", "name": "Центральный федеральный округ"},
                                            {"kind": "province", "name": "Москва"},
                                            {"kind": "locality", "name": "Москва"},
                                            {"kind": "street", "name": "Самотёчная улица"},
                                            {"kind": "house", "name": "7с2"},
                                        ],
                                    },
                                    "AddressDetails": {
                                        "Country": {
                                            "AddressLine": "Россия, Москва, Самотёчная улица, 7с2",
                                            "CountryNameCode": "RU",
                                            "CountryName": "Россия",
                                            "AdministrativeArea": {
                                                "AdministrativeAreaName": "Москва",
                                                "Locality": {
                                                    "LocalityName": "Москва",
                                                    "Thoroughfare": {
                                                        "ThoroughfareName": "Самотёчная улица",
                                                        "Premise": {
                                                            "PremiseNumber": "7с2",
                                                            "PostalCode": {"PostalCodeNumber": "127473"},
                                                        },
                                                    },
                                                },
                                            },
                                        }
                                    },
                                }
                            },
                            "name": "Самотёчная улица, 7с2",
                            "description": "Москва, Россия",
                            "boundedBy": {
                                "Envelope": {
                                    "lowerCorner": "37.613862 55.773606",
                                    "upperCorner": "37.622073 55.778234",
                                }
                            },
                            "Point": {"pos": "37.617968 55.77592"},
                        }
                    }
                ],
            }
        }
    }

    return (
        "Москва, Самотечная улица, дом 7, строение 2",
        geocoder_response,
        [
            {
                "city": "Москва",
                "formatted": "Самотёчная улица, 7с2",
                "description": "Москва, Россия",
                "lat": 55.77592,
                "lon": 37.617968,
            }
        ],
    )
