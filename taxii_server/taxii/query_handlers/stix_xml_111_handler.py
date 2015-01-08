# Copyright (c) 2014, The MITRE Corporation. All rights reserved.
# For license information, see the LICENSE.txt file

from .base_handlers import BaseXmlQueryHandler
from libtaxii.constants import *

class StixXml111QueryHandler(BaseXmlQueryHandler):
    """
    Tmp description
    """
    supported_tevs = [CB_STIX_XML_111]
    supported_cms = [CM_CORE]
    mapping_dict = \
{
  'root_context': {
    'children': {
      'STIX_Package': {
        'has_text': False,
        'namespace': 'http://stix.mitre.org/stix-1',
        'prefix': 'stix',
        'children': {
          'STIX_Header': {
            'has_text': False,
            'namespace': 'http://stix.mitre.org/stix-1',
            'prefix': 'stix',
            'children': {
              'Information_Source': {
                'has_text': False,
                'namespace': 'http://stix.mitre.org/stix-1',
                'prefix': 'stix',
                'children': {
                  'References': {
                    'has_text': False,
                    'namespace': 'http://stix.mitre.org/common-1',
                    'prefix': 'stixCommon',
                    'children': {
                      'Reference': {
                        'has_text': True,
                        'namespace': 'http://stix.mitre.org/common-1',
                        'prefix': 'stixCommon',
                        'children': {},
                      },
                    },
                  },
                  'Contributing_Sources': {
                    'has_text': False,
                    'namespace': 'http://stix.mitre.org/common-1',
                    'prefix': 'stixCommon',
                    'children': {
                      'Source': {
                        'has_text': False,
                        'namespace': 'http://stix.mitre.org/common-1',
                        'prefix': 'stixCommon',
                        'children': {
                          'Role': {
                            'has_text': True,
                            'namespace': 'http://stix.mitre.org/common-1',
                            'prefix': 'stixCommon',
                            'children': {
                              '@type': {
                                'has_text': True,
                                'namespace': 'http://www.w3.org/2001/XMLSchema-instance',
                                'prefix': 'xsi',
                                'children': {},
                              },
                            },
                          },
                          'Identity': {
                            'has_text': False,
                            'namespace': 'http://stix.mitre.org/common-1',
                            'prefix': 'stixCommon',
                            'children': {
                              'Name': {
                                'has_text': True,
                                'namespace': 'http://stix.mitre.org/common-1',
                                'prefix': 'stixCommon',
                                'children': {},
                              },
                            },
                          },
                          'Time': {
                            'has_text': False,
                            'namespace': 'http://stix.mitre.org/common-1',
                            'prefix': 'stixCommon',
                            'children': {
                              'Produced_Time': {
                                'has_text': True,
                                'namespace': 'http://cybox.mitre.org/common-2',
                                'prefix': 'cyboxCommon',
                                'children': {
                                  '@precision': {
                                    'has_text': True,
                                    'namespace': None,
                                    'prefix': None,
                                    'children': {},
                                  },
                                },
                              },
                            },
                          },
                        },
                      },
                    },
                  },
                  'Role': {
                    'has_text': True,
                    'namespace': 'http://stix.mitre.org/common-1',
                    'prefix': 'stixCommon',
                    'children': {
                      '@type': {
                        'has_text': True,
                        'namespace': 'http://www.w3.org/2001/XMLSchema-instance',
                        'prefix': 'xsi',
                        'children': {},
                      },
                    },
                  },
                  'Identity': {
                    'has_text': False,
                    'namespace': 'http://stix.mitre.org/common-1',
                    'prefix': 'stixCommon',
                    'children': {
                      'Name': {
                        'has_text': True,
                        'namespace': 'http://stix.mitre.org/common-1',
                        'prefix': 'stixCommon',
                        'children': {},
                      },
                    },
                  },
                  'Time': {
                    'has_text': False,
                    'namespace': 'http://stix.mitre.org/common-1',
                    'prefix': 'stixCommon',
                    'children': {
                      'Produced_Time': {
                        'has_text': True,
                        'namespace': 'http://cybox.mitre.org/common-2',
                        'prefix': 'cyboxCommon',
                        'children': {
                          '@precision': {
                            'has_text': True,
                            'namespace': None,
                            'prefix': None,
                            'children': {},
                          },
                        },
                      },
                    },
                  },
                },
              },
              'Package_Intent': {
                'has_text': True,
                'namespace': 'http://stix.mitre.org/stix-1',
                'prefix': 'stix',
                'children': {},
              },
              'Description': {
                'has_text': True,
                'namespace': 'http://stix.mitre.org/stix-1',
                'prefix': 'stix',
                'children': {
                  '@structuring_format': {
                    'has_text': True,
                    'namespace': None,
                    'prefix': None,
                    'children': {},
                  },
                },
              },
              'Handling': {
                'has_text': False,
                'namespace': 'http://stix.mitre.org/stix-1',
                'prefix': 'stix',
                'children': {
                  'Marking': {
                    'has_text': False,
                    'namespace': 'http://data-marking.mitre.org/Marking-1',
                    'prefix': 'marking',
                    'children': {
                      'Controlled_Structure': {
                        'has_text': True,
                        'namespace': 'http://data-marking.mitre.org/Marking-1',
                        'prefix': 'marking',
                        'children': {},
                      },
                      'Marking_Structure': {
                        'has_text': False,
                        'namespace': 'http://data-marking.mitre.org/Marking-1',
                        'prefix': 'marking',
                        'children': {
                          '@type': {
                            'has_text': True,
                            'namespace': 'http://www.w3.org/2001/XMLSchema-instance',
                            'prefix': 'xsi',
                            'children': {},
                          },
                          'Terms_Of_Use': {
                            'has_text': True,
                            'namespace': 'http://data-marking.mitre.org/extensions/MarkingStructure#Terms_Of_Use-1',
                            'prefix': 'terms',
                            'children': {},
                          },
                        },
                      },
                    },
                  },
                },
              },
              'Title': {
                'has_text': True,
                'namespace': 'http://stix.mitre.org/stix-1',
                'prefix': 'stix',
                'children': {},
              },
            },
          },
          '@id': {
            'has_text': True,
            'namespace': None,
            'prefix': None,
            'children': {},
          },
          '@timestamp': {
            'has_text': True,
            'namespace': None,
            'prefix': None,
            'children': {},
          },
          'Threat_Actors': {
            'has_text': False,
            'namespace': 'http://stix.mitre.org/stix-1',
            'prefix': 'stix',
            'children': {
              'Threat_Actor': {
                'has_text': False,
                'namespace': 'http://stix.mitre.org/stix-1',
                'prefix': 'stix',
                'children': {
                  '@timestamp': {
                    'has_text': True,
                    'namespace': None,
                    'prefix': None,
                    'children': {},
                  },
                  'Associated_Actors': {
                    'has_text': False,
                    'namespace': 'http://stix.mitre.org/ThreatActor-1',
                    'prefix': 'threat-actor',
                    'children': {
                      'Associated_Actor': {
                        'has_text': False,
                        'namespace': 'http://stix.mitre.org/ThreatActor-1',
                        'prefix': 'threat-actor',
                        'children': {
                          'Confidence': {
                            'has_text': False,
                            'namespace': 'http://stix.mitre.org/common-1',
                            'prefix': 'stixCommon',
                            'children': {
                              'Description': {
                                'has_text': True,
                                'namespace': 'http://stix.mitre.org/common-1',
                                'prefix': 'stixCommon',
                                'children': {
                                  '@structuring_format': {
                                    'has_text': True,
                                    'namespace': None,
                                    'prefix': None,
                                    'children': {},
                                  },
                                },
                              },
                              'Value': {
                                'has_text': True,
                                'namespace': 'http://stix.mitre.org/common-1',
                                'prefix': 'stixCommon',
                                'children': {
                                  '@vocab_name': {
                                    'has_text': True,
                                    'namespace': None,
                                    'prefix': None,
                                    'children': {},
                                  },
                                },
                              },
                            },
                          },
                          'Threat_Actor': {
                            'has_text': False,
                            'namespace': 'http://stix.mitre.org/common-1',
                            'prefix': 'stixCommon',
                            'children': {
                              '@idref': {
                                'has_text': True,
                                'namespace': None,
                                'prefix': None,
                                'children': {},
                              },
                            },
                          },
                          'Relationship': {
                            'has_text': True,
                            'namespace': 'http://stix.mitre.org/common-1',
                            'prefix': 'stixCommon',
                            'children': {},
                          },
                        },
                      },
                    },
                  },
                  'Observed_TTPs': {
                    'has_text': False,
                    'namespace': 'http://stix.mitre.org/ThreatActor-1',
                    'prefix': 'threat-actor',
                    'children': {
                      'Observed_TTP': {
                        'has_text': False,
                        'namespace': 'http://stix.mitre.org/ThreatActor-1',
                        'prefix': 'threat-actor',
                        'children': {
                          'TTP': {
                            'has_text': False,
                            'namespace': 'http://stix.mitre.org/common-1',
                            'prefix': 'stixCommon',
                            'children': {
                              '@idref': {
                                'has_text': True,
                                'namespace': None,
                                'prefix': None,
                                'children': {},
                              },
                              'Behavior': {
                                'has_text': False,
                                'namespace': 'http://stix.mitre.org/TTP-1',
                                'prefix': 'ttp',
                                'children': {
                                  'Malware': {
                                    'has_text': False,
                                    'namespace': 'http://stix.mitre.org/TTP-1',
                                    'prefix': 'ttp',
                                    'children': {
                                      'Malware_Instance': {
                                        'has_text': False,
                                        'namespace': 'http://stix.mitre.org/TTP-1',
                                        'prefix': 'ttp',
                                        'children': {
                                          'Name': {
                                            'has_text': True,
                                            'namespace': 'http://stix.mitre.org/TTP-1',
                                            'prefix': 'ttp',
                                            'children': {},
                                          },
                                        },
                                      },
                                    },
                                  },
                                },
                              },
                              '@type': {
                                'has_text': True,
                                'namespace': 'http://www.w3.org/2001/XMLSchema-instance',
                                'prefix': 'xsi',
                                'children': {},
                              },
                              'Resources': {
                                'has_text': False,
                                'namespace': 'http://stix.mitre.org/TTP-1',
                                'prefix': 'ttp',
                                'children': {
                                  'Infrastructure': {
                                    'has_text': False,
                                    'namespace': 'http://stix.mitre.org/TTP-1',
                                    'prefix': 'ttp',
                                    'children': {
                                      'Observable_Characterization': {
                                        'has_text': False,
                                        'namespace': 'http://stix.mitre.org/TTP-1',
                                        'prefix': 'ttp',
                                        'children': {
                                          '@cybox_major_version': {
                                            'has_text': True,
                                            'namespace': None,
                                            'prefix': None,
                                            'children': {},
                                          },
                                          'Observable': {
                                            'has_text': False,
                                            'namespace': 'http://cybox.mitre.org/cybox-2',
                                            'prefix': 'cybox',
                                            'children': {
                                              'Object': {
                                                'has_text': False,
                                                'namespace': 'http://cybox.mitre.org/cybox-2',
                                                'prefix': 'cybox',
                                                'children': {
                                                  'Properties': {
                                                    'has_text': False,
                                                    'namespace': 'http://cybox.mitre.org/cybox-2',
                                                    'prefix': 'cybox',
                                                    'children': {
                                                      '@type': {
                                                        'has_text': True,
                                                        'namespace': None,
                                                        'prefix': None,
                                                        'children': {},
                                                      },
                                                      'Value': {
                                                        'has_text': True,
                                                        'namespace': 'http://cybox.mitre.org/objects#URIObject-2',
                                                        'prefix': 'URIObject',
                                                        'children': {},
                                                      },
                                                    },
                                                  },
                                                },
                                              },
                                            },
                                          },
                                          '@cybox_minor_version': {
                                            'has_text': True,
                                            'namespace': None,
                                            'prefix': None,
                                            'children': {},
                                          },
                                          '@cybox_update_version': {
                                            'has_text': True,
                                            'namespace': None,
                                            'prefix': None,
                                            'children': {},
                                          },
                                        },
                                      },
                                    },
                                  },
                                },
                              },
                            },
                          },
                          'Relationship': {
                            'has_text': True,
                            'namespace': 'http://stix.mitre.org/common-1',
                            'prefix': 'stixCommon',
                            'children': {},
                          },
                        },
                      },
                    },
                  },
                  '@id': {
                    'has_text': True,
                    'namespace': None,
                    'prefix': None,
                    'children': {},
                  },
                  '@type': {
                    'has_text': True,
                    'namespace': 'http://www.w3.org/2001/XMLSchema-instance',
                    'prefix': 'xsi',
                    'children': {},
                  },
                  'Identity': {
                    'has_text': False,
                    'namespace': 'http://stix.mitre.org/ThreatActor-1',
                    'prefix': 'threat-actor',
                    'children': {
                      'Related_Identities': {
                        'has_text': False,
                        'namespace': 'http://stix.mitre.org/common-1',
                        'prefix': 'stixCommon',
                        'children': {
                          'Related_Identity': {
                            'has_text': False,
                            'namespace': 'http://stix.mitre.org/common-1',
                            'prefix': 'stixCommon',
                            'children': {
                              'Identity': {
                                'has_text': False,
                                'namespace': 'http://stix.mitre.org/common-1',
                                'prefix': 'stixCommon',
                                'children': {
                                  'Name': {
                                    'has_text': True,
                                    'namespace': 'http://stix.mitre.org/common-1',
                                    'prefix': 'stixCommon',
                                    'children': {},
                                  },
                                },
                              },
                              'Relationship': {
                                'has_text': True,
                                'namespace': 'http://stix.mitre.org/common-1',
                                'prefix': 'stixCommon',
                                'children': {},
                              },
                            },
                          },
                        },
                      },
                      'Specification': {
                        'has_text': False,
                        'namespace': 'http://stix.mitre.org/extensions/Identity#CIQIdentity3.0-1',
                        'prefix': 'stix-ciq',
                        'children': {
                          'Relationships': {
                            'has_text': False,
                            'namespace': 'urn:oasis:names:tc:ciq:xpil:3',
                            'prefix': 'xpil',
                            'children': {
                              'Relationship': {
                                'has_text': False,
                                'namespace': 'urn:oasis:names:tc:ciq:xpil:3',
                                'prefix': 'xpil',
                                'children': {
                                  'OrganisationName': {
                                    'has_text': False,
                                    'namespace': 'urn:oasis:names:tc:ciq:xnl:3',
                                    'prefix': 'xnl',
                                    'children': {
                                      'NameElement': {
                                        'has_text': True,
                                        'namespace': 'urn:oasis:names:tc:ciq:xnl:3',
                                        'prefix': 'xnl',
                                        'children': {},
                                      },
                                    },
                                  },
                                  '@RelationshipWithOrganisation': {
                                    'has_text': True,
                                    'namespace': 'urn:oasis:names:tc:ciq:xpil:3',
                                    'prefix': 'xpil',
                                    'children': {},
                                  },
                                },
                              },
                            },
                          },
                          'Addresses': {
                            'has_text': False,
                            'namespace': 'urn:oasis:names:tc:ciq:xpil:3',
                            'prefix': 'xpil',
                            'children': {
                              'Address': {
                                'has_text': False,
                                'namespace': 'urn:oasis:names:tc:ciq:xpil:3',
                                'prefix': 'xpil',
                                'children': {
                                  'Premises': {
                                    'has_text': False,
                                    'namespace': 'urn:oasis:names:tc:ciq:xal:3',
                                    'prefix': 'xal',
                                    'children': {
                                      'NameElement': {
                                        'has_text': True,
                                        'namespace': 'urn:oasis:names:tc:ciq:xal:3',
                                        'prefix': 'xal',
                                        'children': {},
                                      },
                                    },
                                  },
                                  'Country': {
                                    'has_text': False,
                                    'namespace': 'urn:oasis:names:tc:ciq:xal:3',
                                    'prefix': 'xal',
                                    'children': {
                                      'NameElement': {
                                        'has_text': True,
                                        'namespace': 'urn:oasis:names:tc:ciq:xal:3',
                                        'prefix': 'xal',
                                        'children': {},
                                      },
                                    },
                                  },
                                  'AdministrativeArea': {
                                    'has_text': False,
                                    'namespace': 'urn:oasis:names:tc:ciq:xal:3',
                                    'prefix': 'xal',
                                    'children': {
                                      'NameElement': {
                                        'has_text': True,
                                        'namespace': 'urn:oasis:names:tc:ciq:xal:3',
                                        'prefix': 'xal',
                                        'children': {},
                                      },
                                      'SubAdministrativeArea': {
                                        'has_text': False,
                                        'namespace': 'urn:oasis:names:tc:ciq:xal:3',
                                        'prefix': 'xal',
                                        'children': {
                                          'NameElement': {
                                            'has_text': True,
                                            'namespace': 'urn:oasis:names:tc:ciq:xal:3',
                                            'prefix': 'xal',
                                            'children': {},
                                          },
                                        },
                                      },
                                    },
                                  },
                                  'Thoroughfare': {
                                    'has_text': False,
                                    'namespace': 'urn:oasis:names:tc:ciq:xal:3',
                                    'prefix': 'xal',
                                    'children': {
                                      'NameElement': {
                                        'has_text': True,
                                        'namespace': 'urn:oasis:names:tc:ciq:xal:3',
                                        'prefix': 'xal',
                                        'children': {},
                                      },
                                      'Number': {
                                        'has_text': True,
                                        'namespace': 'urn:oasis:names:tc:ciq:xal:3',
                                        'prefix': 'xal',
                                        'children': {},
                                      },
                                    },
                                  },
                                  'Locality': {
                                    'has_text': False,
                                    'namespace': 'urn:oasis:names:tc:ciq:xal:3',
                                    'prefix': 'xal',
                                    'children': {
                                      'NameElement': {
                                        'has_text': True,
                                        'namespace': 'urn:oasis:names:tc:ciq:xal:3',
                                        'prefix': 'xal',
                                        'children': {},
                                      },
                                    },
                                  },
                                },
                              },
                            },
                          },
                          'Qualifications': {
                            'has_text': False,
                            'namespace': 'urn:oasis:names:tc:ciq:xpil:3',
                            'prefix': 'xpil',
                            'children': {
                              'Qualification': {
                                'has_text': False,
                                'namespace': 'urn:oasis:names:tc:ciq:xpil:3',
                                'prefix': 'xpil',
                                'children': {
                                  'QualificationElement': {
                                    'has_text': True,
                                    'namespace': 'urn:oasis:names:tc:ciq:xpil:3',
                                    'prefix': 'xpil',
                                    'children': {},
                                  },
                                },
                              },
                            },
                          },
                          'PartyName': {
                            'has_text': False,
                            'namespace': 'urn:oasis:names:tc:ciq:xpil:3',
                            'prefix': 'xpil',
                            'children': {
                              'PersonName': {
                                'has_text': False,
                                'namespace': 'urn:oasis:names:tc:ciq:xnl:3',
                                'prefix': 'xnl',
                                'children': {
                                  'NameElement': {
                                    'has_text': True,
                                    'namespace': 'urn:oasis:names:tc:ciq:xnl:3',
                                    'prefix': 'xnl',
                                    'children': {},
                                  },
                                  '@Type': {
                                    'has_text': True,
                                    'namespace': 'urn:oasis:names:tc:ciq:xnl:3',
                                    'prefix': 'xnl',
                                    'children': {},
                                  },
                                },
                              },
                              'OrganisationName': {
                                'has_text': False,
                                'namespace': 'urn:oasis:names:tc:ciq:xnl:3',
                                'prefix': 'xnl',
                                'children': {
                                  'NameElement': {
                                    'has_text': True,
                                    'namespace': 'urn:oasis:names:tc:ciq:xnl:3',
                                    'prefix': 'xnl',
                                    'children': {},
                                  },
                                  'SubDivisionName': {
                                    'has_text': True,
                                    'namespace': 'urn:oasis:names:tc:ciq:xnl:3',
                                    'prefix': 'xnl',
                                    'children': {},
                                  },
                                  '@Type': {
                                    'has_text': True,
                                    'namespace': 'urn:oasis:names:tc:ciq:xnl:3',
                                    'prefix': 'xnl',
                                    'children': {},
                                  },
                                },
                              },
                            },
                          },
                          'OrganisationInfo': {
                            'has_text': False,
                            'namespace': 'urn:oasis:names:tc:ciq:xpil:3',
                            'prefix': 'xpil',
                            'children': {
                              '@NumberOfEmployees': {
                                'has_text': True,
                                'namespace': 'urn:oasis:names:tc:ciq:xpil:3',
                                'prefix': 'xpil',
                                'children': {},
                              },
                            },
                          },
                          'Languages': {
                            'has_text': False,
                            'namespace': 'urn:oasis:names:tc:ciq:xpil:3',
                            'prefix': 'xpil',
                            'children': {
                              'Language': {
                                'has_text': True,
                                'namespace': 'urn:oasis:names:tc:ciq:xpil:3',
                                'prefix': 'xpil',
                                'children': {},
                              },
                            },
                          },
                          'Accounts': {
                            'has_text': False,
                            'namespace': 'urn:oasis:names:tc:ciq:xpil:3',
                            'prefix': 'xpil',
                            'children': {
                              'Account': {
                                'has_text': False,
                                'namespace': 'urn:oasis:names:tc:ciq:xpil:3',
                                'prefix': 'xpil',
                                'children': {
                                  'Organisation': {
                                    'has_text': False,
                                    'namespace': 'urn:oasis:names:tc:ciq:xpil:3',
                                    'prefix': 'xpil',
                                    'children': {
                                      'NameElement': {
                                        'has_text': True,
                                        'namespace': 'urn:oasis:names:tc:ciq:xnl:3',
                                        'prefix': 'xnl',
                                        'children': {},
                                      },
                                    },
                                  },
                                  '@Type': {
                                    'has_text': True,
                                    'namespace': 'urn:oasis:names:tc:ciq:xpil:3',
                                    'prefix': 'xpil',
                                    'children': {},
                                  },
                                },
                              },
                            },
                          },
                          'ElectronicAddressIdentifiers': {
                            'has_text': False,
                            'namespace': 'urn:oasis:names:tc:ciq:xpil:3',
                            'prefix': 'xpil',
                            'children': {
                              'ElectronicAddressIdentifier': {
                                'has_text': True,
                                'namespace': 'urn:oasis:names:tc:ciq:xpil:3',
                                'prefix': 'xpil',
                                'children': {
                                  '@Type': {
                                    'has_text': True,
                                    'namespace': 'urn:oasis:names:tc:ciq:xpil:3',
                                    'prefix': 'xpil',
                                    'children': {},
                                  },
                                },
                              },
                            },
                          },
                          'Nationalities': {
                            'has_text': False,
                            'namespace': 'urn:oasis:names:tc:ciq:xpil:3',
                            'prefix': 'xpil',
                            'children': {
                              'Country': {
                                'has_text': False,
                                'namespace': 'urn:oasis:names:tc:ciq:xpil:3',
                                'prefix': 'xpil',
                                'children': {
                                  'NameElement': {
                                    'has_text': True,
                                    'namespace': 'urn:oasis:names:tc:ciq:xal:3',
                                    'prefix': 'xal',
                                    'children': {},
                                  },
                                },
                              },
                            },
                          },
                        },
                      },
                      'Role': {
                        'has_text': True,
                        'namespace': 'http://stix.mitre.org/extensions/Identity#CIQIdentity3.0-1',
                        'prefix': 'stix-ciq',
                        'children': {},
                      },
                      '@type': {
                        'has_text': True,
                        'namespace': 'http://www.w3.org/2001/XMLSchema-instance',
                        'prefix': 'xsi',
                        'children': {},
                      },
                      'Name': {
                        'has_text': True,
                        'namespace': 'http://stix.mitre.org/common-1',
                        'prefix': 'stixCommon',
                        'children': {},
                      },
                    },
                  },
                },
              },
            },
          },
          'TTPs': {
            'has_text': False,
            'namespace': 'http://stix.mitre.org/stix-1',
            'prefix': 'stix',
            'children': {
              'TTP': {
                'has_text': False,
                'namespace': 'http://stix.mitre.org/stix-1',
                'prefix': 'stix',
                'children': {
                  'Title': {
                    'has_text': True,
                    'namespace': 'http://stix.mitre.org/TTP-1',
                    'prefix': 'ttp',
                    'children': {},
                  },
                  'Kill_Chain_Phases': {
                    'has_text': False,
                    'namespace': 'http://stix.mitre.org/TTP-1',
                    'prefix': 'ttp',
                    'children': {
                      'Kill_Chain_Phase': {
                        'has_text': False,
                        'namespace': 'http://stix.mitre.org/common-1',
                        'prefix': 'stixCommon',
                        'children': {
                          '@kill_chain_id': {
                            'has_text': True,
                            'namespace': None,
                            'prefix': None,
                            'children': {},
                          },
                          '@phase_id': {
                            'has_text': True,
                            'namespace': None,
                            'prefix': None,
                            'children': {},
                          },
                        },
                      },
                    },
                  },
                  '@timestamp': {
                    'has_text': True,
                    'namespace': None,
                    'prefix': None,
                    'children': {},
                  },
                  'Intended_Effect': {
                    'has_text': False,
                    'namespace': 'http://stix.mitre.org/TTP-1',
                    'prefix': 'ttp',
                    'children': {
                      'Description': {
                        'has_text': True,
                        'namespace': 'http://stix.mitre.org/common-1',
                        'prefix': 'stixCommon',
                        'children': {
                          '@structuring_format': {
                            'has_text': True,
                            'namespace': None,
                            'prefix': None,
                            'children': {},
                          },
                        },
                      },
                      'Value': {
                        'has_text': True,
                        'namespace': 'http://stix.mitre.org/common-1',
                        'prefix': 'stixCommon',
                        'children': {
                          '@type': {
                            'has_text': True,
                            'namespace': 'http://www.w3.org/2001/XMLSchema-instance',
                            'prefix': 'xsi',
                            'children': {},
                          },
                        },
                      },
                    },
                  },
                  'Related_TTPs': {
                    'has_text': False,
                    'namespace': 'http://stix.mitre.org/TTP-1',
                    'prefix': 'ttp',
                    'children': {
                      'Related_TTP': {
                        'has_text': False,
                        'namespace': 'http://stix.mitre.org/TTP-1',
                        'prefix': 'ttp',
                        'children': {
                          'TTP': {
                            'has_text': False,
                            'namespace': 'http://stix.mitre.org/common-1',
                            'prefix': 'stixCommon',
                            'children': {
                              '@idref': {
                                'has_text': True,
                                'namespace': None,
                                'prefix': None,
                                'children': {},
                              },
                            },
                          },
                          'Relationship': {
                            'has_text': True,
                            'namespace': 'http://stix.mitre.org/common-1',
                            'prefix': 'stixCommon',
                            'children': {},
                          },
                        },
                      },
                    },
                  },
                  'Behavior': {
                    'has_text': False,
                    'namespace': 'http://stix.mitre.org/TTP-1',
                    'prefix': 'ttp',
                    'children': {
                      'Attack_Patterns': {
                        'has_text': False,
                        'namespace': 'http://stix.mitre.org/TTP-1',
                        'prefix': 'ttp',
                        'children': {
                          'Attack_Pattern': {
                            'has_text': False,
                            'namespace': 'http://stix.mitre.org/TTP-1',
                            'prefix': 'ttp',
                            'children': {
                              'Description': {
                                'has_text': True,
                                'namespace': 'http://stix.mitre.org/TTP-1',
                                'prefix': 'ttp',
                                'children': {
                                  '@structuring_format': {
                                    'has_text': True,
                                    'namespace': None,
                                    'prefix': None,
                                    'children': {},
                                  },
                                },
                              },
                              '@capec_id': {
                                'has_text': True,
                                'namespace': None,
                                'prefix': None,
                                'children': {},
                              },
                            },
                          },
                        },
                      },
                      'Malware': {
                        'has_text': False,
                        'namespace': 'http://stix.mitre.org/TTP-1',
                        'prefix': 'ttp',
                        'children': {
                          'Malware_Instance': {
                            'has_text': False,
                            'namespace': 'http://stix.mitre.org/TTP-1',
                            'prefix': 'ttp',
                            'children': {
                              'Type': {
                                'has_text': True,
                                'namespace': 'http://stix.mitre.org/TTP-1',
                                'prefix': 'ttp',
                                'children': {},
                              },
                              'Name': {
                                'has_text': True,
                                'namespace': 'http://stix.mitre.org/TTP-1',
                                'prefix': 'ttp',
                                'children': {},
                              },
                              'Description': {
                                'has_text': True,
                                'namespace': 'http://stix.mitre.org/TTP-1',
                                'prefix': 'ttp',
                                'children': {
                                  '@structuring_format': {
                                    'has_text': True,
                                    'namespace': None,
                                    'prefix': None,
                                    'children': {},
                                  },
                                },
                              },
                            },
                          },
                        },
                      },
                    },
                  },
                  'Victim_Targeting': {
                    'has_text': False,
                    'namespace': 'http://stix.mitre.org/TTP-1',
                    'prefix': 'ttp',
                    'children': {
                      'Identity': {
                        'has_text': False,
                        'namespace': 'http://stix.mitre.org/TTP-1',
                        'prefix': 'ttp',
                        'children': {
                          'Specification': {
                            'has_text': False,
                            'namespace': 'http://stix.mitre.org/extensions/Identity#CIQIdentity3.0-1',
                            'prefix': 'stix-ciq',
                            'children': {
                              'Languages': {
                                'has_text': False,
                                'namespace': 'urn:oasis:names:tc:ciq:xpil:3',
                                'prefix': 'xpil',
                                'children': {
                                  'Language': {
                                    'has_text': True,
                                    'namespace': 'urn:oasis:names:tc:ciq:xpil:3',
                                    'prefix': 'xpil',
                                    'children': {},
                                  },
                                },
                              },
                              'FreeTextLines': {
                                'has_text': False,
                                'namespace': 'urn:oasis:names:tc:ciq:xpil:3',
                                'prefix': 'xpil',
                                'children': {
                                  'FreeTextLine': {
                                    'has_text': True,
                                    'namespace': 'urn:oasis:names:tc:ciq:xpil:3',
                                    'prefix': 'xpil',
                                    'children': {},
                                  },
                                },
                              },
                              'Addresses': {
                                'has_text': False,
                                'namespace': 'urn:oasis:names:tc:ciq:xpil:3',
                                'prefix': 'xpil',
                                'children': {
                                  'Address': {
                                    'has_text': False,
                                    'namespace': 'urn:oasis:names:tc:ciq:xpil:3',
                                    'prefix': 'xpil',
                                    'children': {
                                      'Country': {
                                        'has_text': False,
                                        'namespace': 'urn:oasis:names:tc:ciq:xal:3',
                                        'prefix': 'xal',
                                        'children': {
                                          'NameElement': {
                                            'has_text': True,
                                            'namespace': 'urn:oasis:names:tc:ciq:xal:3',
                                            'prefix': 'xal',
                                            'children': {},
                                          },
                                        },
                                      },
                                    },
                                  },
                                },
                              },
                            },
                          },
                          '@type': {
                            'has_text': True,
                            'namespace': 'http://www.w3.org/2001/XMLSchema-instance',
                            'prefix': 'xsi',
                            'children': {},
                          },
                        },
                      },
                    },
                  },
                  '@id': {
                    'has_text': True,
                    'namespace': None,
                    'prefix': None,
                    'children': {},
                  },
                  '@type': {
                    'has_text': True,
                    'namespace': 'http://www.w3.org/2001/XMLSchema-instance',
                    'prefix': 'xsi',
                    'children': {},
                  },
                  'Resources': {
                    'has_text': False,
                    'namespace': 'http://stix.mitre.org/TTP-1',
                    'prefix': 'ttp',
                    'children': {
                      'Infrastructure': {
                        'has_text': False,
                        'namespace': 'http://stix.mitre.org/TTP-1',
                        'prefix': 'ttp',
                        'children': {
                          'Observable_Characterization': {
                            'has_text': False,
                            'namespace': 'http://stix.mitre.org/TTP-1',
                            'prefix': 'ttp',
                            'children': {
                              '@cybox_major_version': {
                                'has_text': True,
                                'namespace': None,
                                'prefix': None,
                                'children': {},
                              },
                              'Observable': {
                                'has_text': False,
                                'namespace': 'http://cybox.mitre.org/cybox-2',
                                'prefix': 'cybox',
                                'children': {
                                  'Object': {
                                    'has_text': False,
                                    'namespace': 'http://cybox.mitre.org/cybox-2',
                                    'prefix': 'cybox',
                                    'children': {
                                      '@idref': {
                                        'has_text': True,
                                        'namespace': None,
                                        'prefix': None,
                                        'children': {},
                                      },
                                      '@id': {
                                        'has_text': True,
                                        'namespace': None,
                                        'prefix': None,
                                        'children': {},
                                      },
                                      'Properties': {
                                        'has_text': False,
                                        'namespace': 'http://cybox.mitre.org/cybox-2',
                                        'prefix': 'cybox',
                                        'children': {
                                          '@category': {
                                            'has_text': True,
                                            'namespace': None,
                                            'prefix': None,
                                            'children': {},
                                          },
                                          'Address_Value': {
                                            'has_text': True,
                                            'namespace': 'http://cybox.mitre.org/objects#AddressObject-2',
                                            'prefix': 'AddressObject',
                                            'children': {
                                              '@condition': {
                                                'has_text': True,
                                                'namespace': None,
                                                'prefix': None,
                                                'children': {},
                                              },
                                            },
                                          },
                                          '@type': {
                                            'has_text': True,
                                            'namespace': 'http://www.w3.org/2001/XMLSchema-instance',
                                            'prefix': 'xsi',
                                            'children': {},
                                          },
                                        },
                                      },
                                    },
                                  },
                                },
                              },
                              '@cybox_minor_version': {
                                'has_text': True,
                                'namespace': None,
                                'prefix': None,
                                'children': {},
                              },
                            },
                          },
                          'Type': {
                            'has_text': True,
                            'namespace': 'http://stix.mitre.org/TTP-1',
                            'prefix': 'ttp',
                            'children': {},
                          },
                          'Description': {
                            'has_text': True,
                            'namespace': 'http://stix.mitre.org/TTP-1',
                            'prefix': 'ttp',
                            'children': {
                              '@structuring_format': {
                                'has_text': True,
                                'namespace': None,
                                'prefix': None,
                                'children': {},
                              },
                            },
                          },
                        },
                      },
                      'Tools': {
                        'has_text': False,
                        'namespace': 'http://stix.mitre.org/TTP-1',
                        'prefix': 'ttp',
                        'children': {
                          'Tool': {
                            'has_text': False,
                            'namespace': 'http://stix.mitre.org/TTP-1',
                            'prefix': 'ttp',
                            'children': {
                              'Name': {
                                'has_text': True,
                                'namespace': 'http://cybox.mitre.org/common-2',
                                'prefix': 'cyboxCommon',
                                'children': {},
                              },
                              'Description': {
                                'has_text': True,
                                'namespace': 'http://cybox.mitre.org/common-2',
                                'prefix': 'cyboxCommon',
                                'children': {
                                  '@structuring_format': {
                                    'has_text': True,
                                    'namespace': None,
                                    'prefix': None,
                                    'children': {},
                                  },
                                },
                              },
                            },
                          },
                        },
                      },
                    },
                  },
                },
              },
              'Kill_Chains': {
                'has_text': False,
                'namespace': 'http://stix.mitre.org/stix-1',
                'prefix': 'stix',
                'children': {
                  'Kill_Chain': {
                    'has_text': False,
                    'namespace': 'http://stix.mitre.org/common-1',
                    'prefix': 'stixCommon',
                    'children': {
                      '@name': {
                        'has_text': True,
                        'namespace': None,
                        'prefix': None,
                        'children': {},
                      },
                      'Kill_Chain_Phase': {
                        'has_text': False,
                        'namespace': 'http://stix.mitre.org/common-1',
                        'prefix': 'stixCommon',
                        'children': {
                          '@ordinality': {
                            'has_text': True,
                            'namespace': None,
                            'prefix': None,
                            'children': {},
                          },
                          '@name': {
                            'has_text': True,
                            'namespace': None,
                            'prefix': None,
                            'children': {},
                          },
                          '@phase_id': {
                            'has_text': True,
                            'namespace': None,
                            'prefix': None,
                            'children': {},
                          },
                        },
                      },
                      '@id': {
                        'has_text': True,
                        'namespace': None,
                        'prefix': None,
                        'children': {},
                      },
                      '@number_of_phases': {
                        'has_text': True,
                        'namespace': None,
                        'prefix': None,
                        'children': {},
                      },
                      '@definer': {
                        'has_text': True,
                        'namespace': None,
                        'prefix': None,
                        'children': {},
                      },
                    },
                  },
                },
              },
            },
          },
          '@schemaLocation': {
            'has_text': True,
            'namespace': 'http://www.w3.org/2001/XMLSchema-instance',
            'prefix': 'xsi',
            'children': {},
          },
          '@version': {
            'has_text': True,
            'namespace': None,
            'prefix': None,
            'children': {},
          },
        },
      },
    },
  },
}
