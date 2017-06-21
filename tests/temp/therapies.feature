@developed @rules @noserver @nightly @abstractsummaryengine
Feature: Generate Therapy for SNV Report
  In order to display therapy summary in the SNV report
  As the Export module
  I want to generate therapy summary for a given SNV analysis

  Scenario Outline: Generate Therapy for Detected In Variant
    Given a RuleSet with the following therapy rules:
      | drug        | disease_type      | response_to_drugs   | in                    | metastatic | adjuvant |
      | Panitumumab | Colorectal Cancer | Primary sensitivity | KRAS c.35G>T G12V     | NCCN       | NCCN     |
      | Afatinib    | Colorectal Cancer | Primary sensitivity | EGFR Exon 19 Deletion | NCCN       | NCCN     |

    And an "<disease_type>" Analysis with the following results:
      | gene | g_change          | aa_change | decision_result   | confirmation_decision   | is_reported |
      | KRAS | c.35G>T           | G12V      | <decision_result> | <confirmation_decision> | false       |
      | EGFR | c.2239_2241delTTA | L747del   | <decision_result> | <confirmation_decision> | false       |

    And the following Drugs objects:
      | name        | classes                                 |
      | afatinib    | Kinase Inhibitors                       |
      | panitumumab | Immunotherapies, Therapeutic Antibodies |

    And the Analysis belongs to an order that does not have a final report
    When I generate therapy summary
    Then I should get the following results:
      | drug        | drug_class/Afatinib | drug_class/Panitumumab                  | variant_summary                 | response_to_drugs   | setting_name         | setting_value | on_label   | disease_name           |
      | Afatinib    | Kinase Inhibitors   |                                         | EGFR Exon 19 Deletion (L747del) | Primary sensitivity | Metastatic, Adjuvant | NCCN          | <on_label> | <therapy_disease_type> |
      | Panitumumab |                     | Immunotherapies, Therapeutic Antibodies | KRAS G12V                       | Primary sensitivity | Metastatic, Adjuvant | NCCN          | <on_label> | <therapy_disease_type> |

    Examples:
      | disease_type      | therapy_disease_type | decision_result | confirmation_decision | on_label |
      | Colorectal Cancer | Colorectal Cancer    | Mut             | UNDETERMINED          | true     |
      | Colorectal Cancer | Colorectal Cancer    | Returned        | MUT                   | true     |
      | Lung Cancer       | Colorectal Cancer    | Mut             | UNDETERMINED          | false    |
      | Lung Cancer       | Colorectal Cancer    | Returned        | MUT                   | false    |


  Scenario Outline: Generate Therapy for Detected In Variant for Multiple Diseases
    Given a RuleSet with the following therapy rules:
      | drug      | disease_type      | response_to_drugs   | in                    | metastatic | adjuvant |
      | Afatinib  | Colorectal Cancer | Primary sensitivity | EGFR Exon 19 Deletion | NCCN       | NCCN     |
      | Dasatinib | Melanoma          | Primary sensitivity | KRAS c.35G>T G12V     | NCCN       | NCCN     |
      | Erlotinib | GIST              | Primary resistance  | KRAS c.35G>T G12V     | NCCN       | NCCN     |

    And an "<disease_type>" Analysis with the following results:
      | gene | g_change          | aa_change | decision_result | confirmation_decision | is_reported |
      | KRAS | c.35G>T           | G12V      | Mut             | UNDETERMINED          | false       |
      | EGFR | c.2239_2241delTTA | L747del   | Mut             | UNDETERMINED          | false       |


    And the Analysis belongs to an order that does not have a final report
    When I generate therapy summary
    Then I should get the following results (ordered by on_label):
      | drug      | variant_summary                 | response_to_drugs   | setting_name         | setting_value | on_label    | disease_name      |
      | Afatinib  | EGFR Exon 19 Deletion (L747del) | Primary sensitivity | Metastatic, Adjuvant | NCCN          | <on_label1> | Colorectal Cancer |
      | Dasatinib | KRAS G12V                       | Primary sensitivity | Metastatic, Adjuvant | NCCN          | <on_label2> | Melanoma          |

    Examples:
      | disease_type                | on_label1 | on_label2 |
      | Melanoma, Colorectal Cancer | true      | true      |
      | Melanoma                    | false     | true      |
      | Colorectal Cancer           | true      | false     |
      | Lung Cancer                 | false     | false     |


  Scenario Outline: No Therapy for Non-Detected In Variant
    Given a RuleSet with the following therapy rules:
      | drug        | disease_type      | response_to_drugs   | in                    | metastatic | adjuvant |
      | Panitumumab | Colorectal Cancer | Primary sensitivity | KRAS c.35G>T G12V     | NCCN       | NCCN     |
      | Afatinib    | Colorectal Cancer | Primary sensitivity | EGFR Exon 19 Deletion | NCCN       | NCCN     |

    And an "Colorectal Cancer" Analysis with the following results:
      | gene | g_change          | aa_change | decision_result   | confirmation_decision   | is_reported |
      | KRAS | c.35G>T           | G12V      | <decision_result> | <confirmation_decision> | false       |
      | EGFR | c.2239_2241delTTA | L747del   | <decision_result> | <confirmation_decision> | false       |

    And the Analysis belongs to an order that does not have a final report
    When I generate therapy summary
    Then I should get no therapy results

    Examples:
      | decision_result       | confirmation_decision |
      | NONE                  | UNDETERMINED          |
      | ND                    | UNDETERMINED          |
      | FT                    | UNDETERMINED          |
      | Confirm               | UNDETERMINED          |
      | Not_Rep               | UNDETERMINED          |
      | Pending               | UNDETERMINED          |
      | NOT_REVIEWED          | UNDETERMINED          |
      | DETECTED_NOT_REPORTED | UNDETERMINED          |
      | Returned              | UNDETERMINED          |
      | Returned              | NOT_DETECTED          |
      | Returned              | FAILED_TESTING        |
      | Returned              | NOT_REVIEWED          |
      | Returned              | DETECTED_NOT_REPORTED |


  Scenario: Generate Therapy for Amino Acid Rule
    Given a RuleSet with the following therapy rules:
      | drug        | disease_type      | response_to_drugs   | in                    | metastatic |
      | Panitumumab | Colorectal Cancer | Primary sensitivity | EGFR A763_Y764insFQEA | NCCN       |

    And an "Colorectal Cancer" Analysis with the following results:
      | gene | g_change                   | aa_change        | decision_result | confirmation_decision | is_reported |
      | EGFR | c.2290_2291insTTCAAGAAGCCT | A763_Y764insFQEA | Mut             | UNDETERMINED          | false       |

    When I generate therapy summary
    Then I should get the following results:
      | drug        | variant_summary       | response_to_drugs   | setting_name | setting_value | on_label | disease_name      |
      | Panitumumab | EGFR A763_Y764insFQEA | Primary sensitivity | Metastatic   | NCCN          | true     | Colorectal Cancer |


  Scenario Outline: Generate Therapy for Detected Region Therapy Rule
    Given a RuleSet with the following therapy rules:
      | drug        | disease_type      | response_to_drugs   | in                    | metastatic | adjuvant |
      | Panitumumab | Colorectal Cancer | Primary sensitivity | <region_therapy_rule> | NCCN       | NCCN     |

    And an "Colorectal Cancer" Analysis with the following results:
      | gene    | g_change    | aa_change    | decision_result | confirmation_decision | is_reported |
      | EGFR    | <g_change1> | <aa_change1> | Mut             | UNDETERMINED          | false       |
      | <gene2> | <g_change2> | <aa_change2> | Returned        | MUT                   | false       |

    When I generate therapy summary
    Then I should get the following results:
      | drug        | variant_summary   | response_to_drugs   | setting_name         | setting_value | on_label | disease_name      |
      | Panitumumab | <variant_summary> | Primary sensitivity | Metastatic, Adjuvant | NCCN          | true     | Colorectal Cancer |

    Examples:
      | region_therapy_rule                                       | g_change1               | aa_change1    | gene2  | g_change2             | aa_change2   | variant_summary                      |
      | EGFR Mutation                                             | c.89T>A                 | V30D          | KRAS   | c.34G>T               | G12C         | EGFR Mutation (V30D)                 |
      | EGFR Mutation                                             | c.78G>A                 | (=)           | EGFR   | c.2239_2241delTTA     | L747del      | EGFR Mutation (L747del)              |
      | EGFR Exon 19 Deletion                                     | c.2239_2241delTTA       | L747del       | EGFR   | c.79_81delGAA         | E26del       | EGFR Exon 19 Deletion (L747del)      |
      | EGFR Exon 19 Deletion                                     | c.2246_2248delAAG       | E749del       | EGFR   | c.2245G>A             | E749K        | EGFR Exon 19 Deletion (E749del)      |
      | EGFR c.2235-c.2257 regionspartialoverlap Insertion        | c.2245_2246insAAA       | E749_A750insK | EGFR   | c.2246_2248delAAG     | E749del      | EGFR Insertion (E749_A750insK)       |
      | EGFR c.2235-c.2257 regionspartialoverlap Insertion        | c.2245_2246insAAA       | E749_A750insK | EGFR   | c.2258_2259insAAA     | K754dup      | EGFR Insertion (E749_A750insK)       |
      | EGFR Exon 19 c.2235-c.2257 regionspartialoverlap Deletion | c.2232_2240delCAAGGAATT | K745_L747del  | EGFR   | c.2229_2234delTATCAA  | I744_K745del | EGFR Exon 19 Deletion (K745_L747del) |
      | EGFR Exon 19 c.2235-c.2257 Deletion                       | c.2232_2240delCAAGGAATT | K745_L747del  | EGFR   | c.2244_2249delAGAAGC  | E749_A750del | EGFR Exon 19 Deletion (E749_A750del) |
      | PDGFRA Codon 842 Missense                                 | c.78G>A                 | (=)           | PDGFRA | c.2524G>T             | D842Y        | PDGFRA Codon 842 Missense (D842Y)    |
      | PDGFRA Codon 842 Missense                                 | c.78G>A                 | (=)           | PDGFRA | c.2524G>A             | D842N        | PDGFRA Codon 842 Missense (D842N)    |
      | PDGFRA Codon 842 Missense                                 | c.78G>A                 | (=)           | PDGFRA | c.2523_2524delAGinsGT | D842Y        | PDGFRA Codon 842 Missense (D842Y)    |

  Scenario Outline: No Therapy for Codon-Based Region Rule if not missense
    Given a RuleSet with the following therapy rules:
      | drug        | disease_type      | response_to_drugs   | in                        | metastatic | adjuvant |
      | Panitumumab | Colorectal Cancer | Primary sensitivity | PDGFRA Codon 842 Missense | NCCN       | NCCN     |

    And an "Colorectal Cancer" Analysis with the following results:
      | gene   | g_change   | aa_change   | decision_result | confirmation_decision | is_reported |
      | PDGFRA | <g_change> | <aa_change> | Mut             | UNDETERMINED          | false       |

    When I generate therapy summary
    Then I should get no therapy results

    Examples:
      | g_change                      | aa_change         |
      | c.2526C>T                     | (=)               |
      | c.2524_2526delGAC             | D842del           |
      | c.2524_2526delGACinsTGA       | D842*             |
      | c.2521_2526delAGAGACinsCATTAC | R841_D842delinsHY |
      | c.2526_2527delCAinsTC         | I843L             |

  Scenario Outline: Correct Exon number for genes with Exon Numbering Issue
    Given a RuleSet with the following therapy rules:
      | drug      | disease_type | response_to_drugs   | in                    | metastatic | adjuvant |
      | Sunitinib | GIST         | Primary sensitivity | <region_therapy_rule> | NCCN       | NCCN     |

    And an "GIST" Analysis with the following results:
      | gene   | g_change   | aa_change   | decision_result | confirmation_decision | is_reported |
      | <gene> | <g_change> | <aa_change> | Returned        | MUT                   | false       |

    When I generate therapy summary
    Then I should get the following results:
      | drug      | variant_summary   | response_to_drugs   | setting_name         | setting_value | on_label | disease_name |
      | Sunitinib | <variant_summary> | Primary sensitivity | Metastatic, Adjuvant | NCCN          | true     | GIST         |

    Examples:
      | region_therapy_rule     | gene   | g_change          | aa_change | variant_summary                 | notes (no-op)                      |
      | EGFR Exon 19 Deletion   | EGFR   | c.2239_2241delTTA | L747del   | EGFR Exon 19 Deletion (L747del) | No modification to the exon number |
      | PDGFRA Exon 17 Mutation | PDGFRA | c.2536G>T         | D846Y     | PDGFRA Exon 18 Mutation (D846Y) | Exon number incremented by 1       |
      | NPM1 Exon 11 Mutation   | NPM1   | c.880C>T          | L294F     | NPM1 Exon 12 Mutation (L294F)   | Exon number incremented by 1       |
      | NRAS Exon 1 Mutation    | NRAS   | c.35G>T           | G12V      | NRAS Exon 2 Mutation (G12V)     | Exon number incremented by 1       |
      | PIK3CA Exon 9 Mutation  | PIK3CA | c.1633G>A         | E545K     | PIK3CA Exon 10 Mutation (E545K) | Exon number incremented by 1       |
      | KRAS Exon 1 Mutation    | KRAS   | c.35G>T           | G12V      | KRAS Exon 2 Mutation (G12V)     | Exon number incremented by 1       |
      | AKT1 Exon 2 Mutation    | AKT1   | c.49G>A           | E17K      | AKT1 Exon 4 Mutation (E17K)     | Exon number incremented by 2       |
      | APC Exon 15 Mutation    | APC    | c.4348C>T         | R1450*    | APC Exon 16 Mutation (R1450*)   | Exon number incremented by 1       |
      | IDH1 Exon 2 Mutation    | IDH1   | c.394C>G          | R132G     | IDH1 Exon 4 Mutation (R132G)    | Exon number incremented by 2       |
      | CBLB Exon 8 Mutation    | CBLB   | c.1118G>A         | C373Y     | CBLB Exon 9 Mutation (C373Y)    | Exon number incremented by 1       |
      | BCORL1 Exon 3 Mutation  | BCORL1 | c.1115T>C         | L372P     | BCORL1 Exon 4 Mutation (L372P)  | Exon number incremented by 1       |
# NOTE: this list does not include every gene with an override in the code.


  Scenario: Generate Therapy for Multiple Variants On Same Region Therapy Rule
    Given a RuleSet with the following therapy rules:
      | drug        | disease_type | response_to_drugs   | in            | metastatic | adjuvant |
      | Panitumumab | Lung Cancer  | Primary sensitivity | EGFR Mutation | NCCN       | NCCN     |

    And an "Colorectal Cancer" Analysis with the following results:
      | gene | g_change          | aa_change     | decision_result | is_reported |
      | EGFR | c.89T>A           | V30D          | Mut             | false       |
      | EGFR | c.2239_2241delTTA | L747del       | Mut             | false       |
      | EGFR | c.78G>A           | (=)           | Mut             | false       |
      | EGFR | c.2245_2246insAAA | E749_A750insK | Mut             | false       |

    And the Analysis belongs to an order that does not have a final report
    When I generate therapy summary
    Then I should get the following results:
      | drug        | variant_summary                              | response_to_drugs   | setting_name         | setting_value | on_label | disease_name |
      | Panitumumab | EGFR Mutation (V30D, L747del, E749_A750insK) | Primary sensitivity | Metastatic, Adjuvant | NCCN          | false    | Lung Cancer  |



#######################################################################################################
############################################# WILD TYPE ###############################################
#######################################################################################################
  Scenario Outline: Generate Therapy for Wild Type Therapy Rule
    Given the test regions for the SNV test mode include the following genes: KRAS
    And a RuleSet with the following therapy rules:
      | drug        | disease_type      | response_to_drugs   | in                 | metastatic | adjuvant |
      | Panitumumab | Colorectal Cancer | Primary sensitivity | <region> Wild Type | NCCN       | NCCN     |

    And an "Colorectal Cancer" Analysis with the following results:
      | gene   | g_change   | aa_change   | decision_result   | confirmation_decision   | is_reported |
      | <gene> | <g_change> | <aa_change> | <decision_result> | <confirmation_decision> | false       |

    And the Analysis belongs to an order that does not have a final report
    When I generate therapy summary
    Then I should get the following results:
      | drug        | variant_summary            | response_to_drugs   | setting_name         | setting_value | on_label | disease_name      |
      | Panitumumab | <region_display> Wild Type | Primary sensitivity | Metastatic, Adjuvant | NCCN          | true     | Colorectal Cancer |

    Examples:
      | region      | region_display | gene | g_change  | aa_change | decision_result       | confirmation_decision |
      | KRAS        | KRAS           | BRAF | c.1799T>A | V600E     | Mut                   | UNDETERMINED          |
      | KRAS Exon 4 | KRAS Exon 5    | KRAS | c.35G>T   | G12V      | NONE                  | UNDETERMINED          |
      | KRAS Exon 4 | KRAS Exon 5    | KRAS | c.35G>T   | G12V      | Mut                   | UNDETERMINED          |
      | KRAS        | KRAS           | KRAS | c.35G>T   | G12V      | NONE                  | UNDETERMINED          |
      | KRAS        | KRAS           | KRAS | c.35G>T   | G12V      | ND                    | UNDETERMINED          |
      | KRAS        | KRAS           | KRAS | c.35G>T   | G12V      | FT                    | UNDETERMINED          |
      | KRAS        | KRAS           | KRAS | c.35G>T   | G12V      | Confirm               | UNDETERMINED          |
      | KRAS        | KRAS           | KRAS | c.35G>T   | G12V      | NOT_REVIEWED          | UNDETERMINED          |
      | KRAS        | KRAS           | KRAS | c.35G>T   | G12V      | DETECTED_NOT_REPORTED | UNDETERMINED          |
      | KRAS        | KRAS           | KRAS | c.35G>T   | G12V      | Returned              | UNDETERMINED          |
      | KRAS        | KRAS           | KRAS | c.35G>T   | G12V      | Returned              | NOT_DETECTED          |
      | KRAS        | KRAS           | KRAS | c.35G>T   | G12V      | Returned              | FAILED_TESTING        |
      | KRAS        | KRAS           | KRAS | c.35G>T   | G12V      | Returned              | DETECTED_NOT_REPORTED |
      | KRAS        | KRAS           | KRAS | c.35G>T   | G12V      | Returned              | NOT_REVIEWED          |
      | KRAS        | KRAS           | KRAS | c.36T>C   | (=)       | Mut                   | UNDETERMINED          |
      | KRAS        | KRAS           | KRAS | c.36T>C   | (=)       | Pending               | UNDETERMINED          |
      | KRAS        | KRAS           | KRAS | c.36T>C   | (=)       | Returned              | MUT                   |

  Scenario Outline: No Therapy when Wild Type Gene Has Pending or Detected Non-Synonymous Mutation
    Given the test regions for the SNV test mode include the following genes: KRAS
    And a RuleSet with the following therapy rules:
      | drug        | disease_type      | response_to_drugs   | in             | metastatic | adjuvant |
      | Panitumumab | Colorectal Cancer | Primary sensitivity | KRAS Wild Type | NCCN       | NCCN     |

    And an "Colorectal Cancer" Analysis with the following results:
      | gene   | g_change   | aa_change   | decision_result   | confirmation_decision   | is_reported |
      | <gene> | <g_change> | <aa_change> | <decision_result> | <confirmation_decision> | false       |

    And the Analysis belongs to an order that does not have a final report
    When I generate therapy summary
    Then I should get no therapy results

    Examples:
      | gene | g_change | aa_change | decision_result | confirmation_decision |
      | KRAS | c.35G>T  | G12V      | Mut             | UNDETERMINED          |
      | KRAS | c.35G>T  | G12V      | Returned        | MUT                   |
      | KRAS | c.35G>T  | G12V      | Pending         | UNDETERMINED          |

  Scenario: For rule with only wild types- match rule if all in the panel; no match if none are in the panel
    Given the test regions for the SNV test mode include the following genes: BRAF,EGFR,SMO,PTEN
    And a RuleSet with the following therapy rules:
      | drug        | disease_type      | response_to_drugs   | in                               | metastatic |
      | Panitumumab | Colorectal Cancer | Primary sensitivity | BRAF Wild Type                   | NCCN       |
      | Panitumumab | Colorectal Cancer | Primary sensitivity | KRAS Wild Type                   | NCCN       |
      | Panitumumab | Colorectal Cancer | Primary sensitivity | EGFR Wild Type, SMO Wild Type    | NCCN       |
      | Panitumumab | Colorectal Cancer | Primary sensitivity | NRAS Wild Type, APC Wild Type    | NCCN       |
      | Panitumumab | Colorectal Cancer | Primary sensitivity | [PTEN Wild Type, EGFR Mutation]  | NCCN       |
      | Panitumumab | Colorectal Cancer | Primary sensitivity | [CTNNB1 Wild Type, SMO Mutation] | NCCN       |

    And an "Colorectal Cancer" Analysis with the following results:
      | gene | g_change  | aa_change | decision_result | confirmation_decision | is_reported |
      | BRAF | c.1799T>A | V600E     | ND              | UNDETERMINED          | false       |

    And the Analysis belongs to an order that does not have a final report
    When I generate therapy summary
    Then I should get the following results:
      | drug        | variant_summary               | response_to_drugs   | setting_name | setting_value | on_label | disease_name      |
      | Panitumumab | BRAF Wild Type                | Primary sensitivity | Metastatic   | NCCN          | true     | Colorectal Cancer |
      | Panitumumab | EGFR Wild Type::SMO Wild Type | Primary sensitivity | Metastatic   | NCCN          | true     | Colorectal Cancer |
      | Panitumumab | PTEN Wild Type                | Primary sensitivity | Metastatic   | NCCN          | true     | Colorectal Cancer |

  Scenario: For rule with only wild types- match rule if all in the panel; no match if none are in the panel (with reflex)
    Given the test regions for the SNV test mode include the following genes: BRAF,EGFR,SMO,KRAS,NRAS,APC
    And the product uses test regions with the following genes:
      | name | reflex_group |
      | BRAF | 1            |
      | EGFR | 2            |
      | SMO  | 3            |
      | KRAS | 4            |
      | NRAS | 4            |
      | APC  | 5            |

    And the product has reflex enabled
    And it has an SNV Workbench Config with the following tabs and Criteria:
      | tab_name      | criteria      | reflex_groups |
      | BRAF          | reflexgroup:1 | 1             |
      | EGFR          | reflexgroup:2 | 2             |
      | SMO           | reflexgroup:3 | 3             |
      | KRAS and NRAS | reflexgroup:4 | 4             |
      | APC           | reflexgroup:5 | 5             |

    And a RuleSet with the following therapy rules:
      | drug        | disease_type      | response_to_drugs   | in                            | metastatic |
      | Panitumumab | Colorectal Cancer | Primary sensitivity | BRAF Wild Type                | NCCN       |
      | Panitumumab | Colorectal Cancer | Primary sensitivity | KRAS Wild Type                | NCCN       |
      | Panitumumab | Colorectal Cancer | Primary sensitivity | EGFR Wild Type, SMO Wild Type | NCCN       |
      | Panitumumab | Colorectal Cancer | Primary sensitivity | NRAS Wild Type, APC Wild Type | NCCN       |

    And an "Colorectal Cancer" Analysis with the following results:
      | gene | g_change  | aa_change | decision_result | confirmation_decision | tab  | is_reported |
      | BRAF | c.1799T>A | V600E     | ND              | UNDETERMINED          | BRAF | false       |

    And the analysis has the following reflex status:
      | reflex_tabs_open |
      | BRAF::EGFR::SMO  |

    And the Analysis belongs to an order that does not have a final report
    When I generate therapy summary
    Then I should get the following results:
      | drug        | variant_summary               | response_to_drugs   | setting_name | setting_value | on_label | disease_name      |
      | Panitumumab | BRAF Wild Type                | Primary sensitivity | Metastatic   | NCCN          | true     | Colorectal Cancer |
      | Panitumumab | EGFR Wild Type::SMO Wild Type | Primary sensitivity | Metastatic   | NCCN          | true     | Colorectal Cancer |

  Scenario Outline: Display rule when it has at least one detected variant or wild type on the panel, but indicate which wild type genes were not tested
    Given the test regions for the SNV test mode include the following genes: <test_regions>,RET
    And a RuleSet with the following therapy rules:
      | drug        | disease_type      | response_to_drugs   | in                                                  | metastatic |
      | Panitumumab | Colorectal Cancer | Primary sensitivity | EGFR Wild Type, KRAS Wild Type, PTEN Wild Type      | NCCN       |
      | Panitumumab | Colorectal Cancer | Primary sensitivity | NRAS Wild Type, SMO Wild Type, BRAF c.1799T>A V600E | NCCN       |
      | Panitumumab | Colorectal Cancer | Primary sensitivity | [ROS1 Wild Type, EGFR Mutation], RET Wild Type      | NCCN       |

    And an "Colorectal Cancer" Analysis with the following results:
      | gene | g_change  | aa_change | decision_result | confirmation_decision | is_reported |
      | BRAF | c.1799T>A | V600E     | Mut             | UNDETERMINED          | false       |

    And the Analysis belongs to an order that does not have a final report
    When I generate therapy summary
    Then I should get the following results:
      | drug        | variant_summary                                     | response_to_drugs   | setting_name | setting_value | on_label | disease_name      |
      | Panitumumab | <vs1>                                               | Primary sensitivity | Metastatic   | NCCN          | true     | Colorectal Cancer |
      | Panitumumab | <vs2>                                               | Primary sensitivity | Metastatic   | NCCN          | true     | Colorectal Cancer |
      | Panitumumab | RET Wild Type::(ROS1 Wild Type *<i>not tested</i>*) | Primary sensitivity | Metastatic   | NCCN          | true     | Colorectal Cancer |

    Examples:
      | test_regions  | vs1                                                                                        | vs2                                                                                   |
      | EGFR          | EGFR Wild Type::(KRAS Wild Type *<i>not tested</i>*)::(PTEN Wild Type *<i>not tested</i>*) | BRAF V600E::(NRAS Wild Type *<i>not tested</i>*)::(SMO Wild Type *<i>not tested</i>*) |
      | KRAS,NRAS     | KRAS Wild Type::(EGFR Wild Type *<i>not tested</i>*)::(PTEN Wild Type *<i>not tested</i>*) | BRAF V600E::NRAS Wild Type::(SMO Wild Type *<i>not tested</i>*)                       |
      | PTEN,KRAS,SMO | KRAS Wild Type::PTEN Wild Type::(EGFR Wild Type *<i>not tested</i>*)                       | BRAF V600E::SMO Wild Type::(NRAS Wild Type *<i>not tested</i>*)                       |

  Scenario: Display rule when it has at least one detected variaNt or wild type on the panel, but indicate which wild type genes were not tested (with reflex)
    Given the test regions for the SNV test mode include the following genes: EGFR,KRAS,PTEN,NRAS,SMO,BRAF
    And the product uses test regions with the following genes:
      | name | reflex_group |
      | EGFR | 1            |
      | KRAS | 2            |
      | PTEN | 3            |
      | NRAS | 4            |
      | BRAF | 4            |
      | SMO  | 5            |

    And the product has reflex enabled

    And it has an SNV Workbench Config with the following tabs and Criteria:
      | tab_name      | criteria      | reflex_groups |
      | EGFR          | reflexgroup:1 | 1             |
      | KRAS          | reflexgroup:2 | 2             |
      | PTEN          | reflexgroup:3 | 3             |
      | NRAS and BRAF | reflexgroup:4 | 4             |
      | SMO           | reflexgroup:5 | 5             |
      | BRAF          | reflexgroup:6 | 6             |

    And a RuleSet with the following therapy rules:
      | drug        | disease_type      | response_to_drugs   | in                                                  | metastatic |
      | Panitumumab | Colorectal Cancer | Primary sensitivity | EGFR Wild Type, KRAS Wild Type, PTEN Wild Type      | NCCN       |
      | Panitumumab | Colorectal Cancer | Primary sensitivity | NRAS Wild Type, SMO Wild Type, BRAF c.1799T>A V600E | NCCN       |

    And an "Colorectal Cancer" Analysis with the following results:
      | gene | g_change  | aa_change | decision_result | confirmation_decision | tab  | is_reported |
      | BRAF | c.1799T>A | V600E     | Mut             | UNDETERMINED          | BRAF | false       |

    And the analysis has the following reflex status:
      | reflex_tabs_open    |
      | NRAS and BRAF::KRAS |

    And the Analysis belongs to an order that does not have a final report
    When I generate therapy summary
    Then I should get the following results:
      | drug        | variant_summary                                                                            | response_to_drugs   | setting_name | setting_value | on_label | disease_name      |
      | Panitumumab | KRAS Wild Type::(EGFR Wild Type *<i>not tested</i>*)::(PTEN Wild Type *<i>not tested</i>*) | Primary sensitivity | Metastatic   | NCCN          | true     | Colorectal Cancer |
      | Panitumumab | BRAF V600E::NRAS Wild Type::(SMO Wild Type *<i>not tested</i>*)                            | Primary sensitivity | Metastatic   | NCCN          | true     | Colorectal Cancer |

  Scenario: For rule with only wild types- all genes considered to be on the panel if there are no SNV test regions
    Given the Product has no SNV test regions defined
    And a RuleSet with the following therapy rules:
      | drug        | disease_type      | response_to_drugs   | in                            | metastatic |
      | Panitumumab | Colorectal Cancer | Primary sensitivity | BRAF Wild Type                | NCCN       |
      | Panitumumab | Colorectal Cancer | Primary sensitivity | EGFR Wild Type, SMO Wild Type | NCCN       |

    And an "Colorectal Cancer" Analysis with the following results:
      | gene | g_change  | aa_change | decision_result | confirmation_decision | is_reported |
      | BRAF | c.1799T>A | V600E     | ND              | UNDETERMINED          | false       |

    And the Analysis belongs to an order that does not have a final report
    When I generate therapy summary
    Then I should get the following results:
      | drug        | variant_summary               | response_to_drugs   | setting_name | setting_value | on_label | disease_name      |
      | Panitumumab | BRAF Wild Type                | Primary sensitivity | Metastatic   | NCCN          | true     | Colorectal Cancer |
      | Panitumumab | EGFR Wild Type::SMO Wild Type | Primary sensitivity | Metastatic   | NCCN          | true     | Colorectal Cancer |

  Scenario Outline: For rule with wild types using SNaPshot- match rule if gene has any non-failed variants; no match if all variants in gene fail
    Given the test regions for the SNV test mode include the following genes: BRAF,KRAS,EGFR,SMO,NRAS,APC
    And a RuleSet with the following therapy rules:
      | drug        | disease_type      | response_to_drugs   | in                            | metastatic |
      | Panitumumab | Colorectal Cancer | Primary sensitivity | BRAF Wild Type                | NCCN       |
      | Panitumumab | Colorectal Cancer | Primary sensitivity | KRAS Wild Type                | NCCN       |
      | Panitumumab | Colorectal Cancer | Primary sensitivity | EGFR Wild Type, SMO Wild Type | NCCN       |
      | Panitumumab | Colorectal Cancer | Primary sensitivity | NRAS Wild Type, APC Wild Type | NCCN       |

    And an "Colorectal Cancer" Analysis with the following results:
      | gene | g_change              | aa_change | decision_result   | confirmation_decision | is_reported | platform |
      | BRAF | c.1799T>A             | V600E     | <decision_result> | UNDETERMINED          | false       | SNaPshot |
      | KRAS | c.34G>T               | G12C      | FT                | UNDETERMINED          | false       | SNaPshot |
      | KRAS | c.182A>T              | Q61L      | FT                | UNDETERMINED          | false       | SNaPshot |
      | EGFR | c.2156G>C             | G719A     | FT                | UNDETERMINED          | false       | SNaPshot |
      | EGFR | c.2582T>A             | L861Q     | ND                | UNDETERMINED          | false       | SNaPshot |
      | NRAS | c.35G>C               | G12A      | ND                | UNDETERMINED          | false       | SNaPshot |
      | APC  | c.4199_4200delCGinsAA | S1400*    | FT                | UNDETERMINED          | false       | SNaPshot |

    And the Analysis belongs to an order that does not have a final report
    When I generate therapy summary
    Then I should get the following results:
      | drug        | variant_summary                                     | response_to_drugs   | setting_name | setting_value | on_label | disease_name      |
      | Panitumumab | BRAF Wild Type                                      | Primary sensitivity | Metastatic   | NCCN          | true     | Colorectal Cancer |
      | Panitumumab | EGFR Wild Type::SMO Wild Type                       | Primary sensitivity | Metastatic   | NCCN          | true     | Colorectal Cancer |
      | Panitumumab | NRAS Wild Type::(APC Wild Type *<i>not tested</i>*) | Primary sensitivity | Metastatic   | NCCN          | true     | Colorectal Cancer |

    Examples:
      | decision_result       |
      | ND                    |
      | NONE                  |
      | Confirm               |
      | NOT_REVIEWED          |
      | DETECTED_NOT_REPORTED |
      | Returned              |

  Scenario: SNaPshot failed testing and Wild Type, when not all genes are on the panel
    Given the test regions for the SNV test mode include the following genes: EGFR,KRAS,NRAS
    And a RuleSet with the following therapy rules:
      | drug        | disease_type      | response_to_drugs   | in                                             | metastatic |
      | Panitumumab | Colorectal Cancer | Primary sensitivity | EGFR Wild Type, KRAS Wild Type, PTEN Wild Type | NCCN       |
      | Panitumumab | Colorectal Cancer | Primary sensitivity | NRAS Wild Type, SMO Wild Type                  | NCCN       |

    And an "Colorectal Cancer" Analysis with the following results:
      | gene | g_change | aa_change | decision_result | confirmation_decision | is_reported | platform |
      | KRAS | c.34G>T  | G12C      | FT              | UNDETERMINED          | false       | SNaPshot |
      | KRAS | c.182A>T | Q61L      | FT              | UNDETERMINED          | false       | SNaPshot |
      | NRAS | c.35G>C  | G12A      | FT              | UNDETERMINED          | false       | SNaPshot |

    And the Analysis belongs to an order that does not have a final report
    When I generate therapy summary
    Then I should get the following results:
      | drug        | variant_summary                                                                            | response_to_drugs   | setting_name | setting_value | on_label | disease_name      |
      | Panitumumab | EGFR Wild Type::(KRAS Wild Type *<i>not tested</i>*)::(PTEN Wild Type *<i>not tested</i>*) | Primary sensitivity | Metastatic   | NCCN          | true     | Colorectal Cancer |

#######################################################################################################
#######################################################################################################
#######################################################################################################


  Scenario: Generate Therapy when All In Variants Detected
    Given the test regions for the SNV test mode include the following genes: NRAS,SMO
    And a RuleSet with the following therapy rules:
      | drug        | disease_type      | response_to_drugs   | in                                                           | metastatic | adjuvant |
      | Panitumumab | Colorectal Cancer | Primary sensitivity | KRAS c.35G>T G12V, ERBB2 c.2305G>T D769Y                     | NCCN       | NCCN     |
      | Gefitinib   | Colorectal Cancer | Primary sensitivity | EGFR Exon 19 Deletion, KRAS c.35G>T G12V                     | NCCN       | NCCN     |
      | Sunitinib   | Lung Cancer       | Primary sensitivity | EGFR Exon 19 Deletion, BRAF Mutation                         | NCCN       | NCCN     |
      | Afatinib    | Colorectal Cancer | Primary sensitivity | NRAS Wild Type, SMO Wild Type                                | NCCN       | NCCN     |
      | Cetuximab   | Lung Cancer       | Primary sensitivity | NRAS Wild Type, ERBB2 c.2305G>T D769Y, EGFR Exon 19 Deletion | NCCN       | NCCN     |

    And an "Colorectal Cancer" Analysis with the following results:
      | gene  | g_change          | aa_change | decision_result | confirmation_decision | is_reported |
      | KRAS  | c.35G>T           | G12V      | Mut             | UNDETERMINED          | false       |
      | ERBB2 | c.2305G>T         | D769Y     | Returned        | MUT                   | false       |
      | BRAF  | c.1799T>A         | V600E     | Mut             | UNDETERMINED          | false       |
      | EGFR  | c.2239_2241delTTA | L747del   | Returned        | MUT                   | false       |

    And the Analysis belongs to an order that does not have a final report
    When I generate therapy summary
    Then I should get the following results:
      | drug        | variant_summary                                              | response_to_drugs   | setting_name         | setting_value | on_label | disease_name      |
      | Afatinib    | NRAS Wild Type::SMO Wild Type                                | Primary sensitivity | Metastatic, Adjuvant | NCCN          | true     | Colorectal Cancer |
      | Gefitinib   | KRAS G12V::EGFR Exon 19 Deletion (L747del)                   | Primary sensitivity | Metastatic, Adjuvant | NCCN          | true     | Colorectal Cancer |
      | Panitumumab | KRAS G12V::ERBB2 D769Y                                       | Primary sensitivity | Metastatic, Adjuvant | NCCN          | true     | Colorectal Cancer |
      | Cetuximab   | NRAS Wild Type::ERBB2 D769Y::EGFR Exon 19 Deletion (L747del) | Primary sensitivity | Metastatic, Adjuvant | NCCN          | false    | Lung Cancer       |
      | Sunitinib   | EGFR Exon 19 Deletion (L747del)::BRAF Mutation (V600E)       | Primary sensitivity | Metastatic, Adjuvant | NCCN          | false    | Lung Cancer       |

  Scenario Outline: No Therapy when Not All In Variants Detected
    Given the test regions for the SNV test mode include the following genes: SMAD4,SMO
    And a RuleSet with the following therapy rules:
      | drug        | disease_type      | response_to_drugs   | in                                                        | metastatic | adjuvant |
      | Panitumumab | Colorectal Cancer | Primary sensitivity | KRAS c.35G>T G12V, ERBB2 c.2305G>T D769Y                  | NCCN       | NCCN     |
      | Afatinib    | Colorectal Cancer | Primary sensitivity | SMAD4 Wild Type, SMO Wild Type                            | NCCN       | NCCN     |
      | Afatinib    | Colorectal Cancer | Primary sensitivity | SMO Mutation, EGFR Exon 19 Deletion, BRAF c.1799T>A V600E | NCCN       | NCCN     |

    And an "Colorectal Cancer" Analysis with the following results:
      | gene  | g_change           | aa_change   | decision_result  | confirmation_decision | is_reported |
      | KRAS  | c.35G>T            | G12V        | <KRAS_decision>  | <KRAS_confirmation>   | false       |
      | ERBB2 | <g_change>         | <aa_change> | <ERBB2_decision> | <ERBB2_confirmation>  | false       |
      | SMO   | c.118_123delGGGCCT | G40_P41del  | Mut              | UNDETERMINED          | false       |
      | EGFR  | c.2239_2241delTTA  | L747del     | ND               | UNDETERMINED          | false       |
      | BRAF  | c.1799T>A          | V600E       | Mut              | UNDETERMINED          | false       |

    And the Analysis belongs to an order that does not have a final report
    When I generate therapy summary
    Then I should get no therapy results

    Examples:
      | g_change  | aa_change | KRAS_decision | KRAS_confirmation | ERBB2_decision | ERBB2_confirmation |
      | c.2305G>T | D769Y     | NONE          | UNDETERMINED      | Mut            | UNDETERMINED       |
      | c.2305G>T | D769Y     | Mut           | UNDETERMINED      | NOT_DETECTED   | UNDETERMINED       |
      | c.2305G>T | D769Y     | Mut           | UNDETERMINED      | Returned       | NOT_DETECTED       |
      | c.2305G>T | D769Y     | Returned      | MUT               | Pending        | UNDETERMINED       |
      | c.2305G>T | D769Y     | Mut           | UNDETERMINED      | Pending        | UNDETERMINED       |
      | c.2329G>T | V777L     | Mut           | UNDETERMINED      | Mut            | UNDETERMINED       |

  Scenario: Generate Therapy when At Least One Variant in Each In Group Detected
    Given the test regions for the SNV test mode include the following genes: NRAS
    And a RuleSet with the following therapy rules:
      | drug        | disease_type      | response_to_drugs   | in                                                                            | metastatic | adjuvant |
      | Panitumumab | Colorectal Cancer | Primary sensitivity | [KRAS c.35G>T G12V, ERBB2 c.2305G>T D769Y, EGFR c.89T>A V30D]                 | NCCN       | NCCN     |
      | Gefitinib   | Lung Cancer       | Primary sensitivity | [NRAS Wild Type, EGFR Exon 19 Deletion], [BRAF c.1799T>A V600E, SMO Mutation] | NCCN       | NCCN     |

    And an "Colorectal Cancer" Analysis with the following results:
      | gene  | g_change  | aa_change | decision_result | confirmation_decision | is_reported |
      | KRAS  | c.35G>T   | G12V      | Mut             | UNDETERMINED          | false       |
      | ERBB2 | c.2305G>T | D769Y     | Pending         | UNDETERMINED          | false       |
      | BRAF  | c.1799T>A | V600E     | Returned        | MUT                   | false       |

    And the Analysis belongs to an order that does not have a final report
    When I generate therapy summary
    Then I should get the following results:
      | drug        | variant_summary            | response_to_drugs   | setting_name         | setting_value | on_label | disease_name      |
      | Panitumumab | KRAS G12V                  | Primary sensitivity | Metastatic, Adjuvant | NCCN          | true     | Colorectal Cancer |
      | Gefitinib   | NRAS Wild Type::BRAF V600E | Primary sensitivity | Metastatic, Adjuvant | NCCN          | false    | Lung Cancer       |


  Scenario: Generate Multiple Therapies for Multiple Detected Variants in In Group
    Given the test regions for the SNV test mode include the following genes: NRAS
    And a RuleSet with the following therapy rules:
      | drug        | disease_type      | response_to_drugs   | in                                                                            | metastatic | adjuvant |
      | Panitumumab | Colorectal Cancer | Primary resistance  | [KRAS c.34G>T G12C, KRAS c.35G>T G12V]                                        | NCCN       | NCCN     |
      | Gefitinib   | Lung Cancer       | Primary sensitivity | [NRAS Wild Type, EGFR Exon 19 Deletion], [BRAF c.1799T>A V600E, SMO Mutation] | NCCN       | NCCN     |

    And an "Colorectal Cancer" Analysis with the following results:
      | gene | g_change           | aa_change  | decision_result | confirmation_decision | is_reported |
      | KRAS | c.34G>T            | G12C       | Mut             | UNDETERMINED          | false       |
      | KRAS | c.35G>T            | G12V       | Returned        | MUT                   | false       |
      | BRAF | c.1799T>A          | V600E      | Returned        | MUT                   | false       |
      | SMO  | c.118_123delGGGCCT | G40_P41del | Mut             | UNDETERMINED          | false       |
      | EGFR | c.2239_2241delTTA  | L747del    | Mut             | UNDETERMINED          | false       |

    And the Analysis belongs to an order that does not have a final report
    When I generate therapy summary
    Then I should get the following results:
      | drug        | variant_summary                                            | response_to_drugs   | setting_name         | setting_value | on_label | disease_name      |
      | Panitumumab | KRAS G12C                                                  | Primary resistance  | Metastatic, Adjuvant | NCCN          | true     | Colorectal Cancer |
      | Panitumumab | KRAS G12V                                                  | Primary resistance  | Metastatic, Adjuvant | NCCN          | true     | Colorectal Cancer |
      | Gefitinib   | NRAS Wild Type::BRAF V600E                                 | Primary sensitivity | Metastatic, Adjuvant | NCCN          | false    | Lung Cancer       |
      | Gefitinib   | NRAS Wild Type::SMO Mutation (G40_P41del)                  | Primary sensitivity | Metastatic, Adjuvant | NCCN          | false    | Lung Cancer       |
      | Gefitinib   | EGFR Exon 19 Deletion (L747del)::BRAF V600E                | Primary sensitivity | Metastatic, Adjuvant | NCCN          | false    | Lung Cancer       |
      | Gefitinib   | EGFR Exon 19 Deletion (L747del)::SMO Mutation (G40_P41del) | Primary sensitivity | Metastatic, Adjuvant | NCCN          | false    | Lung Cancer       |

  Scenario: No Therapy when In Group Not Detected
    Given the test regions for the SNV test mode include the following genes: NRAS
    And a RuleSet with the following therapy rules:
      | drug        | disease_type      | response_to_drugs   | in                                                                            | metastatic | adjuvant |
      | Panitumumab | Colorectal Cancer | Primary resistance  | [KRAS c.34G>T G12C, KRAS c.35G>T G12V]                                        | NCCN       | NCCN     |
      | Gefitinib   | Lung Cancer       | Primary sensitivity | [NRAS Wild Type, EGFR Exon 19 Deletion], [BRAF c.1799T>A V600E, SMO Mutation] | NCCN       | NCCN     |

    And an "Colorectal Cancer" Analysis with the following results:
      | gene | g_change           | aa_change  | decision_result | confirmation_decision | is_reported |
      | KRAS | c.34G>T            | G12C       | ND              | UNDETERMINED          | false       |
      | KRAS | c.35G>T            | G12V       | Returned        | NOT_DETECTED          | false       |
      | BRAF | c.1799T>A          | V600E      | Returned        | FAILED_TESTING        | false       |
      | SMO  | c.118_123delGGGCCT | G40_P41del | FT              | UNDETERMINED          | false       |
      | EGFR | c.2239_2241delTTA  | L747del    | Mut             | UNDETERMINED          | false       |

    And the Analysis belongs to an order that does not have a final report
    When I generate therapy summary
    Then I should get no therapy results

  Scenario Outline: Generate Therapy when Out Variants Not Detected
    Given a RuleSet with the following therapy rules:
      | drug        | disease_type      | response_to_drugs  | in                    | out                                                         | metastatic | adjuvant |
      | Panitumumab | Colorectal Cancer | Primary resistance | ERBB2 c.2305G>T D769Y | KRAS c.35G>T G12V, KRAS c.34G>T G12C, EGFR Exon 19 Deletion | NCCN       | NCCN     |

    And an "Colorectal Cancer" Analysis for an "SNV" Order with the following results:
      | gene  | g_change          | aa_change | decision_result | confirmation_decision | is_reported |
      | ERBB2 | c.2305G>T         | D769Y     | Mut             | UNDETERMINED          | false       |
      | KRAS  | c.34G>T           | G12C      | <KRAS_decision> | <KRAS_confirmation>   | false       |
      | EGFR  | c.2239_2241delTTA | L747del   | <EGFR_decision> | <EGFR_confirmation>   | false       |

    And the Analysis belongs to an order that does not have a final report
    When I generate therapy summary
    Then I should get the following results:
      | drug        | variant_summary | response_to_drugs  | setting_name         | setting_value | on_label | disease_name      |
      | Panitumumab | ERBB2 D769Y     | Primary resistance | Metastatic, Adjuvant | NCCN          | true     | Colorectal Cancer |

    Examples:
      | KRAS_decision         | KRAS_confirmation     | EGFR_decision         | EGFR_confirmation     |
      | NONE                  | UNDETERMINED          | NONE                  | UNDETERMINED          |
      | ND                    | UNDETERMINED          | ND                    | UNDETERMINED          |
      | FT                    | UNDETERMINED          | FT                    | UNDETERMINED          |
      | Confirm               | UNDETERMINED          | Confirm               | UNDETERMINED          |
      | NOT_REVIEWED          | UNDETERMINED          | NOT_REVIEWED          | UNDETERMINED          |
      | DETECTED_NOT_REPORTED | UNDETERMINED          | DETECTED_NOT_REPORTED | UNDETERMINED          |
      | Returned              | UNDETERMINED          | Returned              | UNDETERMINED          |
      | Returned              | NOT_DETECTED          | Returned              | NOT_DETECTED          |
      | Returned              | FAILED_TESTING        | Returned              | FAILED_TESTING        |
      | Returned              | DETECTED_NOT_REPORTED | Returned              | DETECTED_NOT_REPORTED |
      | Returned              | NOT_REVIEWED          | Returned              | NOT_REVIEWED          |


  Scenario Outline: No Therapy when Any Out Variant Detected Or Pending
    Given a RuleSet with the following therapy rules:
      | drug        | disease_type      | response_to_drugs  | in                    | out                                                         | metastatic | adjuvant |
      | Panitumumab | Colorectal Cancer | Primary resistance | ERBB2 c.2305G>T D769Y | KRAS c.35G>T G12V, KRAS c.34G>T G12C, EGFR Exon 19 Deletion | NCCN       | NCCN     |

    And an "Colorectal Cancer" Analysis for an "SNV" Order with the following results:
      | gene  | g_change          | aa_change   | decision_result | confirmation_decision | is_reported |
      | ERBB2 | c.2305G>T         | D769Y       | Mut             | UNDETERMINED          | false       |
      | KRAS  | <g_change>        | <aa_change> | <KRAS_decision> | <KRAS_confirmation>   | false       |
      | EGFR  | c.2239_2241delTTA | L747del     | <EGFR_decision> | <EGFR_confirmation>   | false       |

    And the Analysis belongs to an order that does not have a final report
    When I generate therapy summary
    Then I should get no therapy results

    Examples:
      | g_change | aa_change | KRAS_decision | KRAS_confirmation | EGFR_decision | EGFR_confirmation |
      | c.35G>T  | G12V      | Mut           | UNDETERMINED      | ND            | UNDETERMINED      |
      | c.34G>T  | G12C      | Mut           | UNDETERMINED      | ND            | UNDETERMINED      |
      | c.34G>T  | G12C      | Returned      | MUT               | ND            | UNDETERMINED      |
      | c.34G>T  | G12C      | Pending       | UNDETERMINED      | ND            | UNDETERMINED      |
      | c.34G>T  | G12C      | ND            | UNDETERMINED      | Pending       | UNDETERMINED      |
      | c.34G>T  | G12C      | ND            | UNDETERMINED      | Mut           | UNDETERMINED      |
      | c.34G>T  | G12C      | ND            | UNDETERMINED      | Returned      | MUT               |

  Scenario Outline: Generate Therapy when Drug Response Is Positive For Other Tumor Type Mutation
    Given a RuleSet with the following therapy rules:
      | drug        | disease_type                 | response_to_drugs   | in                    | metastatic | adjuvant |
      | Panitumumab | Colorectal Cancer            | <response_to_drugs> | KRAS c.34G>T G12C     | NCCN       | NCCN     |
      | Gefitinib   | Basal Cell Carcinoma         | <response_to_drugs> | KRAS c.34G>T G12C     | NCCN       | NCCN     |
      | Afatinib    | Acute Lymphoblastic Leukemia | <response_to_drugs> | EGFR Exon 19 Deletion | NCCN       | NCCN     |

    And an "Lung Cancer" Analysis with the following results:
      | gene | g_change          | aa_change | decision_result | confirmation_decision | is_reported |
      | KRAS | c.34G>T           | G12C      | Mut             | UNDETERMINED          | false       |
      | EGFR | c.2239_2241delTTA | L747del   | Returned        | MUT                   | false       |

    And the Analysis belongs to an order that does not have a final report
    When I generate therapy summary
    Then I should get the following results:
      | drug        | variant_summary                 | response_to_drugs   | setting_name         | setting_value | on_label | disease_name                 |
      | Afatinib    | EGFR Exon 19 Deletion (L747del) | <response_to_drugs> | Metastatic, Adjuvant | NCCN          | false    | Acute Lymphoblastic Leukemia |
      | Gefitinib   | KRAS G12C                       | <response_to_drugs> | Metastatic, Adjuvant | NCCN          | false    | Basal Cell Carcinoma         |
      | Panitumumab | KRAS G12C                       | <response_to_drugs> | Metastatic, Adjuvant | NCCN          | false    | Colorectal Cancer            |

    Examples:
      | response_to_drugs     |
      | Complete response     |
      | Disease free survival |
      | Increase in TTP       |
      | Improved PFS          |
      | Improved OS           |
      | Partial response      |
      | Stable disease        |
      | Clinical response     |
      | CCyR                  |
      | MCyR                  |
      | MMR                   |
      | MHR                   |
      | Primary sensitivity   |
      | Increased sensitivity |
      | Retains sensitivity   |
      | Evidence of activity  |


  Scenario Outline: No Therapy when Drug Response Is Negative For Other Tumor Type Mutation
    Given a RuleSet with the following therapy rules:
      | drug        | disease_type                 | response_to_drugs   | in                    | metastatic | adjuvant |
      | Panitumumab | Colorectal Cancer            | <response_to_drugs> | KRAS c.34G>T G12C     | NCCN       | NCCN     |
      | Afatinib    | Acute Lymphoblastic Leukemia | <response_to_drugs> | EGFR Exon 19 Deletion | NCCN       | NCCN     |

    And an "Lung Cancer" Analysis with the following results:
      | gene | g_change          | aa_change | decision_result | confirmation_decision | is_reported |
      | KRAS | c.34G>T           | G12C      | Mut             | UNDETERMINED          | false       |
      | EGFR | c.2239_2241delTTA | L747del   | Returned        | MUT                   | false       |

    And the Analysis belongs to an order that does not have a final report
    When I generate therapy summary
    Then I should get no therapy results

    Examples:
      | response_to_drugs        |
      | Primary resistance       |
      | Decreased sensitivity    |
      | May decrease sensitivity |
      | Reduced MCyR             |
      | Resistance               |
      | Acquired Resistance      |
      | Secondary Resistance     |


  Scenario: No Therapy For Other Tumor Type when Rule Only Has Wild Type
    Given the test regions for the SNV test mode include the following genes: KRAS,NRAS,SMO,SMAD4
    And a RuleSet with the following therapy rules:
      | drug        | disease_type      | response_to_drugs   | in                                                     | metastatic | adjuvant |
      | Panitumumab | Colorectal Cancer | Primary sensitivity | KRAS Wild Type, NRAS Wild Type                         | NCCN       | NCCN     |
      | Afatinib    | Lung Cancer       | Primary sensitivity | KRAS Wild Type                                         | NCCN       | NCCN     |
      | Gefitinib   | Colorectal Cancer | Primary sensitivity | SMO Wild Type, [SMAD4 Wild Type, BRAF c.1799T>A V600E] | NCCN       | NCCN     |

    And an "Basal Cell Carcinoma" Analysis with the following results:
      | gene | g_change  | aa_change | decision_result | confirmation_decision | is_reported |
      | BRAF | c.1799T>A | V600E     | ND              | UNDETERMINED          | false       |

    And the Analysis belongs to an order that does not have a final report
    When I generate therapy summary
    Then I should get no therapy results

  Scenario: No Therapy For Other Tumor Type when Rule Has Only Out Variants but No In Variants
    Given the test regions for the SNV test mode include the following genes: KRAS
    Given a RuleSet with the following therapy rules:
      | drug        | disease_type      | response_to_drugs   | out                                  | metastatic | adjuvant |
      | Panitumumab | Colorectal Cancer | Primary sensitivity | KRAS c.35G>T G12V, KRAS c.34G>T G12C | NCCN       | NCCN     |

    And an "Basal Cell Carcinoma" Analysis for an "SNV" Order with the following results:
      | gene | g_change          | aa_change | decision_result | confirmation_decision | is_reported |
      | EGFR | c.2239_2241delTTA | L747del   | Mut             | UNDETERMINED          | false       |

    And the Analysis belongs to an order that does not have a final report
    When I generate therapy summary
    Then I should get no therapy results


#####################################################################
################ REGION RULES AND CLASSIFICATION ####################
#####################################################################
  Scenario Outline: Ignore variant classified with prevent_wt_and_region_rules = true when evaluating whether rule with IN region component will trigger
    Given a classification list "significance" with the following decision options:
      | value                  | prevent_wt_and_region_rules |
      | <classification_value> | true                        |

    And a RuleSet with the following therapy rules:
      | drug  | disease_type           | response_to_drugs   | in                        | out | refractory | note (no-op)                              |
      | Drug1 | Acute Myeloid Leukemia | Primary sensitivity | TP53 Missense             |     | NCCN, MCG  | ex of gene mutation type rule             |
      | Drug2 | Acute Myeloid Leukemia | Primary sensitivity | TP53 Codon 72 Missense    |     | NCCN, MCG  | ex of gene codon # mutation type rule     |
      | Drug3 | Acute Myeloid Leukemia | Primary sensitivity | TP53 Exon 3 Mutation      |     | NCCN, MCG  | ex of gene exon # mutation rule           |
      | Drug4 | Acute Myeloid Leukemia | Primary sensitivity | TP53 Exon 3 Deletion      |     | NCCN, MCG  | ex of gene exon # deletion/insertion rule |
      | Drug5 | Acute Myeloid Leukemia | Primary sensitivity | TP53 c.100-c.110 Mutation |     | NCCN, MCG  | ex of range of codon rule                 |

    And an "Acute Myeloid Leukemia" Analysis for an "SNV" Order with the following results:
      | gene | g_change        | aa_change | decision_result | is_reported | mutation_type           | significance           |
      | TP53 | c.215C>G        | P72R      | MUT             | false       | Substitution - Missense | <classification_value> |
      | TP53 | c.322_324delGGT | G108del   | MUT             | false       | Deletion - In Frame     | <classification_value> |
      | TP53 | c.105G>C        | L35F      | MUT             | false       | Substitution - Missense | <classification_value> |

    When I generate therapy summary
    Then I should get no therapy results

    Examples:
      | classification_value |
      | Uncertain            |
      | Sunflower            |

  Scenario: Do not ignore variant classified with prevent_wt_and_region_rules = false when evaluating whether rule with IN region components will trigger
    Given a classification list "significance" with the following decision options:
      | value  | prevent_wt_and_region_rules |
      | Benign | false                       |

    And a RuleSet with the following therapy rules:
      | drug  | disease_type           | response_to_drugs   | in                        | out | refractory | note (no-op)                              |
      | Drug1 | Acute Myeloid Leukemia | Primary sensitivity | TP53 Missense             |     | NCCN, MCG  | ex of gene mutation type rule             |
      | Drug2 | Acute Myeloid Leukemia | Primary sensitivity | TP53 Codon 72 Missense    |     | NCCN, MCG  | ex of gene codon # mutation type rule     |
      | Drug3 | Acute Myeloid Leukemia | Primary sensitivity | TP53 Exon 3 Mutation      |     | NCCN, MCG  | ex of gene exon # mutation rule           |
      | Drug4 | Acute Myeloid Leukemia | Primary sensitivity | TP53 Exon 3 Deletion      |     | NCCN, MCG  | ex of gene exon # deletion/insertion rule |
      | Drug5 | Acute Myeloid Leukemia | Primary sensitivity | TP53 c.100-c.110 Mutation |     | NCCN, MCG  | ex of range of codon rule                 |

    And an "Acute Myeloid Leukemia" Analysis for an "SNV" Order with the following results:
      | gene | g_change        | aa_change | decision_result | is_reported | mutation_type           | significance |
      | TP53 | c.215C>G        | P72R      | MUT             | false       | Substitution - Missense | Benign       |
      | TP53 | c.322_324delGGT | G108del   | MUT             | false       | Deletion - In Frame     | Benign       |
      | TP53 | c.215C>T        | P72L      | MUT             | false       | Substitution - Missense |              |
      | TP53 | c.105G>C        | L35F      | MUT             | false       | Substitution - Missense | Benign       |

    When I generate therapy summary
    Then I should get the following results:
      | drug  | variant_summary                                  | response_to_drugs   | setting_name | setting_value | on_label | disease_name           |
      | Drug1 | TP53 Missense (P72R, P72L, L35F)                 | Primary sensitivity | Refractory   | NCCN, MCG     | true     | Acute Myeloid Leukemia |
      | Drug2 | TP53 Codon 72 Missense (P72R, P72L)              | Primary sensitivity | Refractory   | NCCN, MCG     | true     | Acute Myeloid Leukemia |
      | Drug3 | TP53 Exon 4 Mutation (P72R, G108del, P72L, L35F) | Primary sensitivity | Refractory   | NCCN, MCG     | true     | Acute Myeloid Leukemia |
      | Drug4 | TP53 Exon 4 Deletion (G108del)                   | Primary sensitivity | Refractory   | NCCN, MCG     | true     | Acute Myeloid Leukemia |
      | Drug5 | TP53 Mutation (L35F)                             | Primary sensitivity | Refractory   | NCCN, MCG     | true     | Acute Myeloid Leukemia |

  Scenario: Ignore variant classified with prevent_wt_and_region_rules = true when evaluating whether rule with OUT region component will trigger
    Given the test regions for the SNV test mode include the following genes: TP53
    And a classification list "significance" with the following decision options:
      | value         | prevent_wt_and_region_rules |
      | Likely Benign | true                        |

    And a RuleSet with the following therapy rules:
      | drug  | disease_type           | response_to_drugs   | in | out                    | refractory | note (no-op)                              |
      | Drug1 | Acute Myeloid Leukemia | Primary sensitivity |    | TP53 Missense          | NCCN, MCG  | ex of gene mutation type rule             |
      | Drug2 | Acute Myeloid Leukemia | Primary sensitivity |    | TP53 Codon 72 Missense | NCCN, MCG  | ex of gene codon # mutation type rule     |
      | Drug3 | Acute Myeloid Leukemia | Primary sensitivity |    | TP53 Exon 3 Mutation   | NCCN, MCG  | ex of gene exon # mutation rule           |
      | Drug4 | Acute Myeloid Leukemia | Primary sensitivity |    | TP53 Exon 3 Deletion   | NCCN, MCG  | ex of gene exon # deletion/insertion rule |

    And an "Acute Myeloid Leukemia" Analysis for an "SNV" Order with the following results:
      | gene | g_change        | aa_change | decision_result | is_reported | mutation_type           | significance  |
      | TP53 | c.215C>G        | P72R      | MUT             | false       | Substitution - Missense | Likely Benign |
      | TP53 | c.322_324delGGT | G108del   | MUT             | false       | Deletion - In Frame     | Likely Benign |

    When I generate therapy summary
    Then I should get the following results:
      | drug  | variant_summary                         | response_to_drugs   | setting_name | setting_value | on_label | disease_name           |
      | Drug1 | Relevant alterations not detected: TP53 | Primary sensitivity | Refractory   | NCCN, MCG     | true     | Acute Myeloid Leukemia |
      | Drug2 | Relevant alterations not detected: TP53 | Primary sensitivity | Refractory   | NCCN, MCG     | true     | Acute Myeloid Leukemia |
      | Drug3 | Relevant alterations not detected: TP53 | Primary sensitivity | Refractory   | NCCN, MCG     | true     | Acute Myeloid Leukemia |
      | Drug4 | Relevant alterations not detected: TP53 | Primary sensitivity | Refractory   | NCCN, MCG     | true     | Acute Myeloid Leukemia |

  Scenario: Do not ignore variant classified with prevent_wt_and_region_rules = false when evaluating whether rule with OUT region component will trigger
    Given the test regions for the SNV test mode include the following genes: TP53
    And a classification list "significance" with the following decision options:
      | value     | prevent_wt_and_region_rules |
      | Uncertain | false                       |

    And a RuleSet with the following therapy rules:
      | drug  | disease_type           | response_to_drugs   | in | out                    | refractory | note (no-op)                              |
      | Drug1 | Acute Myeloid Leukemia | Primary sensitivity |    | TP53 Missense          | NCCN, MCG  | ex of gene mutation type rule             |
      | Drug2 | Acute Myeloid Leukemia | Primary sensitivity |    | TP53 Codon 72 Missense | NCCN, MCG  | ex of gene codon # mutation type rule     |
      | Drug3 | Acute Myeloid Leukemia | Primary sensitivity |    | TP53 Exon 3 Mutation   | NCCN, MCG  | ex of gene exon # mutation rule           |
      | Drug4 | Acute Myeloid Leukemia | Primary sensitivity |    | TP53 Exon 3 Deletion   | NCCN, MCG  | ex of gene exon # deletion/insertion rule |

    And an "Acute Myeloid Leukemia" Analysis for an "SNV" Order with the following results:
      | gene | g_change        | aa_change | decision_result | is_reported | mutation_type           | significance |
      | TP53 | c.215C>G        | P72R      | MUT             | false       | Substitution - Missense | Uncertain    |
      | TP53 | c.322_324delGGT | G108del   | MUT             | false       | Deletion - In Frame     | Uncertain    |

    When I generate therapy summary
    Then I should get no therapy results

  Scenario: Ignore variant classified with prevent_wt_and_region_rules = true when evaluating whether rule with WT region component will trigger
    Given the test regions for the SNV test mode include the following genes: TP53
    And a classification list "significance" with the following decision options:
      | value      | prevent_wt_and_region_rules |
      | Pathogenic | true                        |

    And a RuleSet with the following therapy rules:
      | drug  | disease_type           | response_to_drugs   | in             | out | refractory | note (no-op)              |
      | Drug1 | Acute Myeloid Leukemia | Primary sensitivity | TP53 Wild Type |     | NCCN, MCG  | ex of gene wild type rule |

    And an "Acute Myeloid Leukemia" Analysis for an "SNV" Order with the following results:
      | gene | g_change | aa_change | decision_result | is_reported | mutation_type           | significance |
      | TP53 | c.215C>G | P72R      | MUT             | false       | Substitution - Missense | Pathogenic   |

    When I generate therapy summary
    Then I should get the following results:
      | drug  | variant_summary | response_to_drugs   | setting_name | setting_value | on_label | disease_name           |
      | Drug1 | TP53 Wild Type  | Primary sensitivity | Refractory   | NCCN, MCG     | true     | Acute Myeloid Leukemia |


  Scenario: Do not ignore variant classified with prevent_wt_and_region_rules = false when evaluating whether rule with WT region component will trigger
    Given the test regions for the SNV test mode include the following genes: TP53
    And a classification list "significance" with the following decision options:
      | value     | prevent_wt_and_region_rules |
      | Uncertain | false                       |

    And a RuleSet with the following therapy rules:
      | drug  | disease_type           | response_to_drugs   | in             | out | refractory | note (no-op)              |
      | Drug1 | Acute Myeloid Leukemia | Primary sensitivity | TP53 Wild Type |     | NCCN, MCG  | ex of gene wild type rule |

    And an "Acute Myeloid Leukemia" Analysis for an "SNV" Order with the following results:
      | gene | g_change | aa_change | decision_result | is_reported | mutation_type           | classification |
      | TP53 | c.215C>G | P72R      | MUT             | false       | Substitution - Missense | Uncertain      |

    When I generate therapy summary
    Then I should get no therapy results

  Scenario Outline: Generate therapy for rule that directly mentions gene variant (and variant is detected), regardless of prevent_wt_and_region_rules value
    Given a classification list "significance" with the following decision options:
      | value     | prevent_wt_and_region_rules   |
      | uncertain | <prevent_wt_and_region_rules> |

    And a RuleSet with the following therapy rules:
      | drug  | disease_type           | response_to_drugs   | in                    | out | refractory | note (no-op)            |
      | Drug1 | Acute Myeloid Leukemia | Primary sensitivity | TP53 c.215C>G P72R    |     | NCCN, MCG  | ex of gene variant rule |
      | Drug2 | Acute Myeloid Leukemia | Primary sensitivity | EGFR A763_Y764insFQEA |     | NCCN, MCG  | ex of amino acid rule   |

    And an "Acute Myeloid Leukemia" Analysis for an "SNV" Order with the following results:
      | gene | g_change                   | aa_change        | decision_result | is_reported | mutation_type           | classification |
      | TP53 | c.215C>G                   | P72R             | MUT             | false       | Substitution - Missense | Uncertain      |
      | EGFR | c.2290_2291insTTCAAGAAGCCT | A763_Y764insFQEA | MUT             | false       | Substitution - Missense | Uncertain      |

    When I generate therapy summary
    Then I should get the following results:
      | drug  | variant_summary       | response_to_drugs   | setting_name | setting_value | on_label | disease_name           |
      | Drug1 | TP53 P72R             | Primary sensitivity | Refractory   | NCCN, MCG     | true     | Acute Myeloid Leukemia |
      | Drug2 | EGFR A763_Y764insFQEA | Primary sensitivity | Refractory   | NCCN, MCG     | true     | Acute Myeloid Leukemia |

    Examples:
      | prevent_wt_and_region_rules |
      | true                        |
      | false                       |



##########################################################################################################
################ SUPPRESS RULE IF IT IS A SUBSET OF ANOTHER MATCHED RULE FOR THE SAME DRUG ###############
##########################################################################################################
# If two therapy rules for the same DRUG AND DISEASE are fully matched, and the matched variants of one rule are a subset of the other, then suppress the smaller rule

########################## Scenarios where suppression does not occur ################################

  @suppression
  Scenario: Do Not Suppress a single-variant rule when 2-variant combo involving that same variant is also detected for an order with multiple diseases
    Given the test regions for the SNV test mode include the following genes: EGFR, BRAF
    And a RuleSet with the following therapy rules:
      | drug       | disease_type      | response_to_drugs   | in                                         | out | metastatic |
      | Crizotinib | Lung Cancer       | Primary sensitivity | EGFR c.2573T>G L858R                       |     | NCCN       |
      | Crizotinib | Colorectal Cancer | Primary Sensitivity | BRAF c.1799T>A V600E                       |     | NCCN       |
      | Crizotinib | Lung Cancer       | Primary sensitivity | BRAF c.1799T>A V600E, EGFR c.2573T>G L858R |     | NCCN       |

    And an "Lung Cancer, Colorectal Cancer" Analysis for an "SNV" Order with the following results:
      | test_mode | gene | g_change  | aa_change | decision_result | is_reported |
      | SNV       | EGFR | c.2573T>G | L858R     | Mut             | false       |
      | SNV       | BRAF | c.1799T>A | V600E     | Mut             | false       |

    And the Analysis belongs to an order that does not have a final report
    When I generate therapy summary
    Then I should get the following results:
      | drug       | variant_summary        | response_to_drugs   | setting_name | setting_value | on_label | disease_name      |
      | Crizotinib | BRAF V600E             | Primary sensitivity | Metastatic   | NCCN          | true     | Colorectal Cancer |
      | Crizotinib | BRAF V600E::EGFR L858R | Primary sensitivity | Metastatic   | NCCN          | true     | Lung Cancer       |


  @suppression
  Scenario Outline: No suppression when the two rules have the same variants
    Given the test regions for the SNV test mode include the following genes: CEBPA
    And a RuleSet with the following therapy rules:
      | drug     | disease_type           | response_to_drugs   | in    | out    | metastatic |
      | Afatinib | Acute Myeloid Leukemia | Primary sensitivity | <in1> | <out1> | NCCN       |
      | Afatinib | Acute Myeloid Leukemia | Primary resistance  | <in2> | <out2> | FDA        |

    And an "Acute Myeloid Leukemia" Analysis for an "SNV+CTX" Order with the following results:
      | test_mode | gene | g_change  | aa_change | fusion_partner | mutation_type | decision_result | is_reported |
      | SNV       | FLT3 | c.2506A>T | I836F     |                |               | Mut             | false       |
      | CTX       | CBFB |           |           | MYH11          | Fusion        | Positive        | false       |

    And the Analysis belongs to an order that does not have a final report
    When I generate therapy summary
    Then I should get the following results:
      | drug     | variant_summary   | response_to_drugs   | setting_name | setting_value | on_label | disease_name           |
      | Afatinib | <variant_summary> | Primary sensitivity | Metastatic   | NCCN          | true     | Acute Myeloid Leukemia |
      | Afatinib | <variant_summary> | Primary resistance  | Metastatic   | FDA           | true     | Acute Myeloid Leukemia |

    Examples:
      | in1                                                     | out1           | in2                                                             | out2           | variant_summary                          |
      | FLT3 c.2506A>T I836F                                    |                | FLT3 c.2506A>T I836F                                            |                | FLT3 I836F                               |
      |                                                         | CEBPA Mutation |                                                                 | CEBPA Mutation | Relevant alterations not detected: CEBPA |
      | CBFB-MYH11 Fusion, FLT3 c.2506A>T I836F                 | CEBPA Mutation | CBFB-MYH11 Fusion, FLT3 c.2506A>T I836F                         | CEBPA Mutation | FLT3 I836F::CBFB-MYH11 Fusion            |
      | FLT3 c.2506A>T I836F                                    |                | [FLT3 c.2506A>T I836F, FLT3 c.2503G>C D835H]                    |                | FLT3 I836F                               |
      | FLT3 c.2506A>T I836F, [RUNX1 Fusion, CBFB-MYH11 Fusion] |                | [FLT3 c.2506A>T I836F, FLT3 c.2503G>C D835H], CBFB-MYH11 Fusion |                | FLT3 I836F::CBFB-MYH11 Fusion            |

  @suppression
  Scenario Outline: No suppression when two rules are for different "off-label" diseases
    Given a RuleSet with the following therapy rules:
      | drug     | disease_type           | response_to_drugs   | in    | out    | metastatic |
      | Afatinib | Acute Myeloid Leukemia | Primary sensitivity | <in1> | <out1> | NCCN       |
      | Afatinib | Lung Cancer            | Primary sensitivity | <in2> | <out2> | NCCN       |

    And an "Colorectal Cancer" Analysis with the following results:
      | test_mode | gene | g_change  | aa_change | fusion_partner | mutation_type | decision_result | is_reported |
      | SNV       | FLT3 | c.2506A>T | I836F     |                |               | Mut             | false       |
      | CTX       | CBFB |           |           | MYH11          | Fusion        | Positive        | false       |

    And the Analysis belongs to an order that does not have a final report
    When I generate therapy summary
    Then I should get the following results:
      | drug     | variant_summary    | response_to_drugs   | setting_name | setting_value | on_label | disease_name           |
      | Afatinib | <variant_summary1> | Primary sensitivity | Metastatic   | NCCN          | false    | Acute Myeloid Leukemia |
      | Afatinib | <variant_summary2> | Primary sensitivity | Metastatic   | NCCN          | false    | Lung Cancer            |

    Examples:
      | in1                                     | out1 | in2                                     | out2 | variant_summary1              | variant_summary2              |
      | FLT3 c.2506A>T I836F                    |      | FLT3 c.2506A>T I836F, CBFB-MYH11 Fusion |      | FLT3 I836F                    | FLT3 I836F::CBFB-MYH11 Fusion |
      | FLT3 c.2506A>T I836F, CBFB-MYH11 Fusion |      | FLT3 c.2506A>T I836F                    |      | FLT3 I836F::CBFB-MYH11 Fusion | FLT3 I836F                    |


  @suppression
  Scenario Outline: No suppression when two rules are for different "off-label" diseases, but you only get one rule anyway, because we don't show rules with only out variants for Other Tumor Type
    Given the test regions for the SNV test mode include the following genes: CEBPA
    And a RuleSet with the following therapy rules:
      | drug     | disease_type           | response_to_drugs   | in    | out    | metastatic |
      | Afatinib | Acute Myeloid Leukemia | Primary sensitivity | <in1> | <out1> | NCCN       |
      | Afatinib | Lung Cancer            | Primary sensitivity | <in2> | <out2> | NCCN       |

    And an "Colorectal Cancer" Analysis for an "SNV_CTX" Order with the following results:
      | test_mode | gene | g_change  | aa_change | fusion_partner | mutation_type | decision_result | is_reported |
      | SNV       | FLT3 | c.2506A>T | I836F     |                |               | Mut             | false       |
      | CTX       | CBFB |           |           | MYH11          | Fusion        | Positive        | false       |

    And the Analysis belongs to an order that does not have a final report
    When I generate therapy summary
    Then I should get the following results:
      | drug     | variant_summary   | response_to_drugs   | setting_name | setting_value | on_label | disease_name |
      | Afatinib | <variant_summary> | Primary sensitivity | Metastatic   | NCCN          | false    | <disease>    |

    Examples:
      | in1               | out1           | in2               | out2           | variant_summary   | disease                |
      | CBFB-MYH11 Fusion | CEBPA Mutation |                   | CEBPA Mutation | CBFB-MYH11 Fusion | Acute Myeloid Leukemia |
      |                   | CEBPA Mutation | CBFB-MYH11 Fusion | CEBPA Mutation | CBFB-MYH11 Fusion | Lung Cancer            |


  @suppression
  Scenario Outline: No suppression when two rules are for different drugs
    Given the test regions for the SNV test mode include the following genes: CEBPA
    And a RuleSet with the following therapy rules:
      | drug      | disease_type | response_to_drugs   | in    | out    | metastatic |
      | Afatinib  | Lung Cancer  | Primary sensitivity | <in1> | <out1> | NCCN       |
      | Erlotinib | Lung Cancer  | Primary resistance  | <in2> | <out2> | NCCN       |

    And an "Lung Cancer" Analysis for an "SNV+CTX" Order with the following results:
      | test_mode | gene | g_change  | aa_change | fusion_partner | mutation_type | decision_result | is_reported |
      | SNV       | FLT3 | c.2506A>T | I836F     |                |               | Mut             | false       |
      | CTX       | CBFB |           |           | MYH11          | Fusion        | Positive        | false       |

    And the Analysis belongs to an order that does not have a final report
    When I generate therapy summary
    Then I should get the following results:
      | drug      | variant_summary    | response_to_drugs   | setting_name | setting_value | on_label | disease_name |
      | Afatinib  | <variant_summary1> | Primary sensitivity | Metastatic   | NCCN          | true     | Lung Cancer  |
      | Erlotinib | <variant_summary2> | Primary resistance  | Metastatic   | NCCN          | true     | Lung Cancer  |

    Examples:
      | in1                                     | out1           | in2                                     | out2           | variant_summary1                         | variant_summary2                         |
      | FLT3 c.2506A>T I836F                    |                | FLT3 c.2506A>T I836F, CBFB-MYH11 Fusion |                | FLT3 I836F                               | FLT3 I836F::CBFB-MYH11 Fusion            |
      | FLT3 c.2506A>T I836F, CBFB-MYH11 Fusion |                | FLT3 c.2506A>T I836F                    |                | FLT3 I836F::CBFB-MYH11 Fusion            | FLT3 I836F                               |
      | CBFB-MYH11 Fusion                       | CEBPA Mutation |                                         | CEBPA Mutation | CBFB-MYH11 Fusion                        | Relevant alterations not detected: CEBPA |
      |                                         | CEBPA Mutation | CBFB-MYH11 Fusion                       | CEBPA Mutation | Relevant alterations not detected: CEBPA | CBFB-MYH11 Fusion                        |

  @suppression
  Scenario Outline: No suppression when superset rule is not triggered
    Given the test regions for the SNV test mode include the following genes: CEBPA
    And a RuleSet with the following therapy rules:
      | drug     | disease_type | response_to_drugs   | in    | out    | metastatic |
      | Afatinib | Lung Cancer  | Primary sensitivity | <in1> | <out1> | NCCN       |
      | Afatinib | Lung Cancer  | Primary sensitivity | <in2> | <out2> | NCCN       |

    And an "Lung Cancer" Analysis for an "SNV+CTX" Order with the following results:
      | test_mode | gene | g_change  | aa_change | fusion_partner | mutation_type | decision_result | is_reported |
      | SNV       | FLT3 | c.2506A>T | I836F     |                |               | Mut             | false       |
      | CTX       | CBFB |           |           | MYH11          | Fusion        | Positive        | false       |

    And the Analysis belongs to an order that does not have a final report
    When I generate therapy summary
    Then I should get the following results:
      | drug     | variant_summary   | response_to_drugs   | setting_name | setting_value | on_label | disease_name |
      | Afatinib | <variant_summary> | Primary sensitivity | Metastatic   | NCCN          | true     | Lung Cancer  |

    Examples:
      | in1                  | out1           | in2                              | out2                 | variant_summary                          |
      | FLT3 c.2506A>T I836F |                | FLT3 c.2506A>T I836F, ALK Fusion |                      | FLT3 I836F                               |
      |                      | CEBPA Mutation | ALK Fusion                       | CEBPA Mutation       | Relevant alterations not detected: CEBPA |
      | CBFB-MYH11 Fusion    |                | CBFB-MYH11 Fusion                | FLT3 c.2506A>T I836F | CBFB-MYH11 Fusion                        |


  @suppression
  Scenario Outline: No suppression when one rule is not a subset of the other rule
    Given a RuleSet with the following therapy rules:
      | drug     | disease_type | response_to_drugs   | in    | out    | metastatic |
      | Afatinib | Lung Cancer  | Primary sensitivity | <in1> | <out1> | NCCN       |
      | Afatinib | Lung Cancer  | Primary sensitivity | <in2> | <out2> | NCCN       |

    And an "Lung Cancer" Analysis for an "SNV+CTX" Order with the following results:
      | test_mode | gene  | g_change  | aa_change | fusion_partner | mutation_type | decision_result | is_reported |
      | SNV       | FLT3  | c.2506A>T | I836F     |                |               | Mut             | false       |
      | SNV       | ERBB2 | c.2305G>T | D769Y     |                |               | Mut             | false       |
      | CTX       | CBFB  |           |           | MYH11          | Fusion        | Positive        | false       |

    And the Analysis belongs to an order that does not have a final report
    When I generate therapy summary
    Then I should get the following results:
      | drug     | variant_summary    | response_to_drugs   | setting_name | setting_value | on_label | disease_name |
      | Afatinib | <variant_summary1> | Primary sensitivity | Metastatic   | NCCN          | true     | Lung Cancer  |
      | Afatinib | <variant_summary2> | Primary sensitivity | Metastatic   | NCCN          | true     | Lung Cancer  |

    Examples:
      | in1                                         | out1           | in2                                      | out2           | variant_summary1        | variant_summary2               |
      | FLT3 c.2506A>T I836F                        |                | CBFB-MYH11 Fusion                        |                | FLT3 I836F              | CBFB-MYH11 Fusion              |
      | FLT3 c.2506A>T I836F, ERBB2 c.2305G>T D769Y |                | CBFB-MYH11 Fusion, ERBB2 c.2305G>T D769Y |                | FLT3 I836F::ERBB2 D769Y | CBFB-MYH11 Fusion::ERBB2 D769Y |
      | FLT3 c.2506A>T I836F                        | CEBPA Mutation | CBFB-MYH11 Fusion                        | CEBPA Mutation | FLT3 I836F              | CBFB-MYH11 Fusion              |
      | FLT3 c.2506A>T I836F                        | CEBPA Mutation | FLT3 c.2506A>T I836F                     | KIT Mutation   | FLT3 I836F              | FLT3 I836F                     |
      | FLT3 c.2506A>T I836F, ERBB2 c.2305G>T D769Y | CEBPA Mutation | FLT3 c.2506A>T I836F, CBFB-MYH11 Fusion  | CEBPA Mutation | FLT3 I836F::ERBB2 D769Y | FLT3 I836F::CBFB-MYH11 Fusion  |
######################################################################################################



########################## Scenarios where suppression does occur ####################################
  @suppression
  Scenario Outline: Suppress single-variant rule when 2-variant combo involving that same variant is also detected, for the same "on-label" disease
    Given the test regions for the SNV test mode include the following genes: CEBPA,KIT
    And a RuleSet with the following therapy rules:
      | drug     | disease_type | response_to_drugs   | in    | out    | metastatic |
      | Afatinib | Lung Cancer  | Primary sensitivity | <in1> | <out1> | NCCN       |
      | Afatinib | Lung Cancer  | Primary resistance  | <in2> | <out2> | NCCN       |

    And an "Lung Cancer" Analysis for an "SNV+CTX" Order with the following results:
      | test_mode | gene | g_change  | aa_change | fusion_partner | mutation_type | decision_result | is_reported |
      | SNV       | FLT3 | c.2506A>T | I836F     |                |               | Mut             | false       |
      | SNV       | EGFR | c.89T>A   | V30D      |                |               | Mut             | false       |
      | CTX       | CBFB |           |           | MYH11          | Fusion        | Positive        | false       |

    And the Analysis belongs to an order that does not have a final report
    When I generate therapy summary
    Then I should get the following results:
      | drug     | variant_summary   | response_to_drugs  | setting_name | setting_value | on_label | disease_name |
      | Afatinib | <variant_summary> | Primary resistance | Metastatic   | NCCN          | true     | Lung Cancer  |

    Examples:
      | in1                  | out1           | in2                                     | out2                         | variant_summary                               |
      | FLT3 c.2506A>T I836F |                | FLT3 c.2506A>T I836F, EGFR c.89T>A V30D |                              | FLT3 I836F::EGFR V30D                         |
      | FLT3 c.2506A>T I836F |                | FLT3 c.2506A>T I836F                    | CEBPA Mutation               | FLT3 I836F                                    |
      |                      | CEBPA Mutation | FLT3 c.2506A>T I836F                    | CEBPA Mutation               | FLT3 I836F                                    |
      |                      | CEBPA Mutation |                                         | CEBPA Mutation, KIT Mutation | Relevant alterations not detected: CEBPA, KIT |
      | CBFB-MYH11 Fusion    |                | CBFB-MYH11 Fusion                       | CEBPA Mutation               | CBFB-MYH11 Fusion                             |
      |                      | ALK Fusion     | CBFB-MYH11 Fusion                       | ALK Fusion                   | CBFB-MYH11 Fusion                             |

  @suppression
  Scenario Outline: Suppress single-variant rule when 2-variant combo involving that same variant is also detected, for the same "off-label" disease
    Given the test regions for the SNV test mode include the following genes: CEBPA
    Given a RuleSet with the following therapy rules:
      | drug     | disease_type | response_to_drugs   | in    | out    | metastatic |
      | Afatinib | Lung Cancer  | Primary sensitivity | <in1> | <out1> | NCCN       |
      | Afatinib | Lung Cancer  | Complete response   | <in2> | <out2> | NCCN       |

    And an "Colorectal Cancer" Analysis for an "SNV+CTX" Order with the following results:
      | test_mode | gene | g_change  | aa_change | fusion_partner | mutation_type | decision_result | is_reported |
      | SNV       | FLT3 | c.2506A>T | I836F     |                |               | Mut             | false       |
      | SNV       | EGFR | c.89T>A   | V30D      |                |               | Mut             | false       |
      | CTX       | CBFB |           |           | MYH11          | Fusion        | Positive        | false       |

    And the Analysis belongs to an order that does not have a final report
    When I generate therapy summary
    Then I should get the following results:
      | drug     | variant_summary   | response_to_drugs | setting_name | setting_value | on_label | disease_name |
      | Afatinib | <variant_summary> | Complete response | Metastatic   | NCCN          | false    | Lung Cancer  |

    Examples:
      | in1                  | out1           | in2                                     | out2           | variant_summary       |
      | FLT3 c.2506A>T I836F |                | FLT3 c.2506A>T I836F, EGFR c.89T>A V30D |                | FLT3 I836F::EGFR V30D |
      | FLT3 c.2506A>T I836F |                | FLT3 c.2506A>T I836F                    | CEBPA Mutation | FLT3 I836F            |
      |                      | CEBPA Mutation | FLT3 c.2506A>T I836F                    | CEBPA Mutation | FLT3 I836F            |
      | CBFB-MYH11 Fusion    |                | CBFB-MYH11 Fusion                       | CEBPA Mutation | CBFB-MYH11 Fusion     |
      |                      | ALK Fusion     | CBFB-MYH11 Fusion                       | ALK Fusion     | CBFB-MYH11 Fusion     |

  @suppression
  Scenario: No therapy when off-label suppression results in a rule with no in-variants
    Given the test regions for the SNV test mode include the following genes: CEBPA,KIT
    And a RuleSet with the following therapy rules:
      | drug     | disease_type | response_to_drugs   | in | out                          | metastatic |
      | Afatinib | Lung Cancer  | Primary sensitivity |    | CEBPA Mutation               | NCCN       |
      | Afatinib | Lung Cancer  | Complete response   |    | CEBPA Mutation, KIT Mutation | NCCN       |

    And an "Colorectal Cancer" Analysis with the following results:
      | test_mode | gene | g_change  | aa_change | fusion_partner | mutation_type | decision_result | is_reported |
      | SNV       | FLT3 | c.2506A>T | I836F     |                |               | Mut             | false       |

    And the Analysis belongs to an order that does not have a final report
    When I generate therapy summary
    Then I should get no therapy results


  @suppression
  Scenario Outline: No therapy when suppression results in only an off-label therapy with negative drug response
    Given the test regions for the SNV test mode include the following genes: CEBPA,KIT
    And a RuleSet with the following therapy rules:
      | drug     | disease_type | response_to_drugs   | in    | out    | metastatic |
      | Afatinib | Lung Cancer  | Primary sensitivity | <in1> | <out1> | NCCN       |
      | Afatinib | Lung Cancer  | Primary resistance  | <in2> | <out2> | NCCN       |

    And an "Colorectal Cancer" Analysis for an "SNV+CTX" Order with the following results:
      | test_mode | gene | g_change  | aa_change | fusion_partner | mutation_type | decision_result | is_reported |
      | SNV       | FLT3 | c.2506A>T | I836F     |                |               | Mut             | false       |
      | SNV       | EGFR | c.89T>A   | V30D      |                |               | Mut             | false       |
      | CTX       | CBFB |           |           | MYH11          | Fusion        | Positive        | false       |

    And the Analysis belongs to an order that does not have a final report
    When I generate therapy summary
    Then I should get no therapy results

    Examples:
      | in1                  | out1           | in2                                     | out2                         |
      | FLT3 c.2506A>T I836F |                | FLT3 c.2506A>T I836F, EGFR c.89T>A V30D |                              |
      | FLT3 c.2506A>T I836F |                | FLT3 c.2506A>T I836F                    | CEBPA Mutation               |
      |                      | CEBPA Mutation | FLT3 c.2506A>T I836F                    | CEBPA Mutation               |
      |                      | CEBPA Mutation |                                         | CEBPA Mutation, KIT Mutation |
      | CBFB-MYH11 Fusion    |                | CBFB-MYH11 Fusion                       | CEBPA Mutation               |
      |                      | ALK Fusion     | CBFB-MYH11 Fusion                       | ALK Fusion                   |


  @suppression
  Scenario Outline: Suppress any rule when its detected variants are a subset of another triggered rule for the same disease
    Given the test regions for the SNV test mode include the following genes: CEBPA,KIT
    And a RuleSet with the following therapy rules:
      | drug     | disease_type | response_to_drugs   | in    | out    | metastatic |
      | Afatinib | Lung Cancer  | Primary sensitivity | <in1> | <out1> | NCCN       |
      | Afatinib | Lung Cancer  | Primary resistance  | <in2> | <out2> | NCCN       |

    And an "Lung Cancer" Analysis for an "SNV+CTX" Order with the following results:
      | test_mode | gene | g_change  | aa_change | fusion_partner | mutation_type | decision_result | is_reported |
      | SNV       | FLT3 | c.2506A>T | I836F     |                |               | Mut             | false       |
      | SNV       | EGFR | c.89T>A   | V30D      |                |               | Mut             | false       |
      | CTX       | CBFB |           |           | MYH11          | Fusion        | Positive        | false       |
      | CTX       | ALK  |           |           |                | Inversion     | Positive        | false       |

    And the Analysis belongs to an order that does not have a final report
    When I generate therapy summary
    Then I should get the following results:
      | drug     | variant_summary   | response_to_drugs  | setting_name | setting_value | on_label | disease_name |
      | Afatinib | <variant_summary> | Primary resistance | Metastatic   | NCCN          | true     | Lung Cancer  |

    Examples:
      | in1                                 | out1                         | in2                                                                       | out2                                     | variant_summary                                         |
      | FLT3 c.2506A>T I836F                |                              | FLT3 c.2506A>T I836F, EGFR c.89T>A V30D, ALK Inversion                    |                                          | FLT3 I836F::EGFR V30D::ALK Inversion                    |
      | FLT3 c.2506A>T I836F                |                              | FLT3 c.2506A>T I836F                                                      | CEBPA Mutation, KIT Mutation             | FLT3 I836F                                              |
      |                                     | CEBPA Mutation               | FLT3 c.2506A>T I836F                                                      | CEBPA Mutation, Complex karyotype        | FLT3 I836F                                              |
      | FLT3 c.2506A>T I836F, ALK Inversion |                              | FLT3 c.2506A>T I836F, ALK Inversion, EGFR c.89T>A V30D                    |                                          | FLT3 I836F::ALK Inversion::EGFR V30D                    |
      | ALK Inversion                       | CEBPA Mutation               | ALK Inversion, CBFB-MYH11 Fusion                                          | CEBPA Mutation                           | ALK Inversion::CBFB-MYH11 Fusion                        |
      | ALK Inversion                       | CEBPA Mutation               | ALK Inversion                                                             | CEBPA Mutation, KIT Mutation             | ALK Inversion                                           |
      |                                     | CEBPA Mutation, KIT Mutation | ALK Inversion                                                             | CEBPA Mutation, KIT Mutation             | ALK Inversion                                           |
      | FLT3 c.2506A>T I836F, ALK Inversion |                              | FLT3 c.2506A>T I836F, ALK Inversion, EGFR c.89T>A V30D                    | CEBPA Mutation                           | FLT3 I836F::ALK Inversion::EGFR V30D                    |
      | FLT3 c.2506A>T I836F, ALK Inversion |                              | FLT3 c.2506A>T I836F, ALK Inversion                                       | CEBPA Mutation, KIT Mutation             | FLT3 I836F::ALK Inversion                               |
      | FLT3 c.2506A>T I836F, ALK Inversion |                              | FLT3 c.2506A>T I836F, ALK Inversion, EGFR c.89T>A V30D, CBFB-MYH11 Fusion |                                          | FLT3 I836F::ALK Inversion::EGFR V30D::CBFB-MYH11 Fusion |
      |                                     | CEBPA Mutation, KIT Mutation | ALK Inversion                                                             | CEBPA Mutation, KIT Mutation, ALK Fusion | ALK Inversion                                           |
      | FLT3 c.2506A>T I836F, ALK Inversion | CEBPA Mutation               | FLT3 c.2506A>T I836F, ALK Inversion, CBFB-MYH11 Fusion                    | CEBPA Mutation                           | FLT3 I836F::ALK Inversion::CBFB-MYH11 Fusion            |

  @suppression
  Scenario Outline: Suppress rule based on detected variants, ignoring any non-detected variants in an in-variant group
    Given the test regions for the SNV test mode include the following genes: CEBPA
    Given a RuleSet with the following therapy rules:
      | drug     | disease_type | response_to_drugs   | in    | out    | metastatic |
      | Afatinib | Lung Cancer  | Primary sensitivity | <in1> | <out1> | NCCN       |
      | Afatinib | Lung Cancer  | Primary resistance  | <in2> | <out2> | NCCN       |

    And an "Lung Cancer" Analysis for an "SNV+CTX" Order with the following results:
      | test_mode | gene | g_change  | aa_change | fusion_partner | mutation_type | decision_result | is_reported |
      | SNV       | FLT3 | c.2506A>T | I836F     |                |               | Mut             | false       |
      | SNV       | EGFR | c.89T>A   | V30D      |                |               | Mut             | false       |
      | CTX       | CBFB |           |           | MYH11          | Fusion        | Positive        | false       |

    And the Analysis belongs to an order that does not have a final report
    When I generate therapy summary
    Then I should get the following results:
      | drug     | variant_summary   | response_to_drugs  | setting_name | setting_value | on_label | disease_name |
      | Afatinib | <variant_summary> | Primary resistance | Metastatic   | NCCN          | true     | Lung Cancer  |

    Examples:
      | in1                                    | out1           | in2                                                                     | out2           | variant_summary       |
      | [FLT3 c.2506A>T I836F, CEBPA Mutation] |                | FLT3 c.2506A>T I836F, EGFR c.89T>A V30D                                 |                | FLT3 I836F::EGFR V30D |
      | FLT3 c.2506A>T I836F                   |                | [CEBPA Mutation, FLT3 c.2506A>T I836F], [RET Fusion, EGFR c.89T>A V30D] |                | FLT3 I836F::EGFR V30D |
      | FLT3 c.2506A>T I836F                   |                | FLT3 c.2506A>T I836F, [RET Fusion, EGFR c.89T>A V30D]                   |                | FLT3 I836F::EGFR V30D |
      | [FLT3 c.2506A>T I836F, KIT Mutation]   |                | [CEBPA Mutation, FLT3 c.2506A>T I836F], [RET Fusion, EGFR c.89T>A V30D] |                | FLT3 I836F::EGFR V30D |
      | [FLT3 c.2506A>T I836F, KIT Mutation]   |                | [FLT3 c.2506A>T I836F, RET Fusion]                                      | CEBPA Mutation | FLT3 I836F            |
      |                                        | CEBPA Mutation | [FLT3 c.2506A>T I836F, RET Fusion]                                      | CEBPA Mutation | FLT3 I836F            |
######################################################################################################


################################## Some more examples ################################################
  @suppression
  Scenario: Show rule matched on an in-group, even if other variants in the in-group are suppressed
    Given a RuleSet with the following therapy rules:
      | drug     | disease_type | response_to_drugs   | in                                                           | out | metastatic |
      | Afatinib | Lung Cancer  | Primary sensitivity | [FLT3 c.2506A>T I836F, CBFB-MYH11 Fusion, EGFR c.89T>A V30D] |     | NCCN       |
      | Afatinib | Lung Cancer  | Primary resistance  | FLT3 c.2506A>T I836F, CBFB-MYH11 Fusion                      |     | NCCN       |

    And an "Lung Cancer" Analysis with the following results:
      | test_mode | gene | g_change  | aa_change | fusion_partner | mutation_type | decision_result | is_reported |
      | SNV       | FLT3 | c.2506A>T | I836F     |                |               | Mut             | false       |
      | SNV       | EGFR | c.89T>A   | V30D      |                |               | Mut             | false       |
      | CTX       | CBFB |           |           | MYH11          | Fusion        | Positive        | false       |

    And the Analysis belongs to an order that does not have a final report
    When I generate therapy summary
    Then I should get the following results:
      | drug     | variant_summary               | response_to_drugs   | setting_name | setting_value | on_label | disease_name |
      | Afatinib | EGFR V30D                     | Primary sensitivity | Metastatic   | NCCN          | true     | Lung Cancer  |
      | Afatinib | FLT3 I836F::CBFB-MYH11 Fusion | Primary resistance  | Metastatic   | NCCN          | true     | Lung Cancer  |


  @suppression
  Scenario: Multiple layered subset rules suppressed
    Given a RuleSet with the following therapy rules:
      | drug     | disease_type | response_to_drugs   | in                                                       | out | metastatic |
      | Afatinib | Lung Cancer  | Primary sensitivity | FLT3 c.2503G>C D835H                                     |     | NCCN       |
      | Afatinib | Lung Cancer  | Primary resistance  | FLT3 c.2503G>C D835H, BCR-ABL1 Fusion                    |     | NCCN       |
      | Afatinib | Lung Cancer  | Complete Response   | FLT3 c.2503G>C D835H, BCR-ABL1 Fusion, EGFR c.89T>A V30D |     | NCCN       |

    And an "Lung Cancer" Analysis with the following results:
      | test_mode | gene | g_change  | aa_change | fusion_partner | mutation_type | decision_result | is_reported |
      | SNV       | FLT3 | c.2503G>C | D835H     |                |               | Mut             | false       |
      | SNV       | EGFR | c.89T>A   | V30D      |                |               | Mut             | false       |
      | CTX       | BCR  |           |           | ABL1           | Fusion        | Positive        | false       |

    And the Analysis belongs to an order that does not have a final report
    When I generate therapy summary
    Then I should get the following results:
      | drug     | variant_summary                        | response_to_drugs | setting_name | setting_value | on_label | disease_name |
      | Afatinib | FLT3 D835H::BCR-ABL1 Fusion::EGFR V30D | Complete response | Metastatic   | NCCN          | true     | Lung Cancer  |

  @suppression
  Scenario: No Therapy when Single Variant Therapy Is Also Part Of Detected Combo Therapy With Same Drug
    Given a RuleSet with the following therapy rules:
      | drug        | disease_type      | response_to_drugs   | in                                       | out               | metastatic |
      | Panitumumab | Colorectal Cancer | Primary sensitivity | KRAS c.34G>T G12C, ERBB2 c.2305G>T D769Y |                   | NCCN       |
      | Panitumumab | Colorectal Cancer | Primary resistance  | KRAS c.34G>T G12C                        |                   | NCCN       |
      | Panitumumab | Colorectal Cancer | Primary sensitivity | ERBB2 c.2305G>T D769Y                    |                   | NCCN       |
      | Afatinib    | Colorectal Cancer | Primary sensitivity | KRAS c.34G>T G12C                        |                   | NCCN       |
      | Panitumumab | Lung Cancer       | Primary sensitivity | KRAS c.34G>T G12C                        |                   | NCCN       |
      | Gefitinib   | Colorectal Cancer | Primary sensitivity | EGFR Exon 19 Deletion                    |                   | NCCN       |
      | Gefitinib   | Colorectal Cancer | Primary resistance  | EGFR Exon 19 Deletion, SMO Wild Type     |                   | NCCN       |
      | Cetuximab   | Colorectal Cancer | Primary resistance  | BRAF c.1799T>A V600E                     | EGFR c.89T>A V30D | NCCN       |
      | Cetuximab   | Colorectal Cancer | Primary sensitivity | BRAF c.1799T>A V600E                     |                   | NCCN       |

    And an "Colorectal Cancer" Analysis for an "SNV" Order with the following results:
      | gene  | g_change          | aa_change | decision_result | confirmation_decision | is_reported |
      | KRAS  | c.34G>T           | G12C      | Mut             | UNDETERMINED          | false       |
      | ERBB2 | c.2305G>T         | D769Y     | Mut             | UNDETERMINED          | false       |
      | EGFR  | c.2239_2241delTTA | L747del   | Mut             | UNDETERMINED          | false       |
      | BRAF  | c.1799T>A         | V600E     | Mut             | UNDETERMINED          | false       |

    And the Analysis belongs to an order that does not have a final report
    When I generate therapy summary
    Then I should get the following results:
      | drug        | variant_summary                                | response_to_drugs   | setting_name | setting_value | on_label | disease_name      |
      | Afatinib    | KRAS G12C                                      | Primary sensitivity | Metastatic   | NCCN          | true     | Colorectal Cancer |
      | Panitumumab | KRAS G12C::ERBB2 D769Y                         | Primary sensitivity | Metastatic   | NCCN          | true     | Colorectal Cancer |
      | Cetuximab   | BRAF V600E                                     | Primary resistance  | Metastatic   | NCCN          | true     | Colorectal Cancer |
      | Gefitinib   | EGFR Exon 19 Deletion (L747del)::SMO Wild Type | Primary resistance  | Metastatic   | NCCN          | true     | Colorectal Cancer |

##########################################################################################################
##########################################################################################################
##########################################################################################################

  Scenario Outline: No Therapy for Other Tumor Type when the same drug is triggered For Tumor Type
    Given the test regions for the SNV test mode include the following genes: NRAS
    And a RuleSet with the following therapy rules:
      | drug        | disease_type      | response_to_drugs   | in                    | out | metastatic |
      | Afatinib    | Colorectal Cancer | Primary sensitivity | KRAS c.34G>T G12C     |     | NCCN       |
      | Afatinib    | Colorectal Cancer | Primary resistance  | BRAF c.1799T>A V600E  |     | NCCN       |
      | Afatinib    | Lung Cancer       | Primary sensitivity | KRAS c.34G>T G12C     |     | NCCN       |
      | Gefitinib   | Colorectal Cancer | Primary resistance  | EGFR Exon 19 Deletion |     | NCCN       |
      | Gefitinib   | Lung Cancer       | Primary sensitivity | ERBB2 c.2305G>T D769Y |     | FDA        |
      | Gefitinib   | Lung Cancer       | Primary sensitivity | NRAS Wild Type        |     | NCCN       |
      | Panitumumab | Lung Cancer       | Primary sensitivity | EGFR c.89T>A V30D     |     | NCCN       |
      | <ftt_drug>  | Colorectal Cancer | Primary sensitivity | EGFR c.2573T>G L858R  |     | FDA        |
      | <ott_drug>  | GIST              | Primary sensitivity | EGFR c.2155G>A G719S  |     | FDA        |

    And an "Colorectal Cancer" Analysis with the following results:
      | gene  | g_change          | aa_change | decision_result | confirmation_decision | is_reported |
      | KRAS  | c.34G>T           | G12C      | Mut             | UNDETERMINED          | false       |
      | BRAF  | c.1799T>A         | V600E     | Mut             | UNDETERMINED          | false       |
      | ERBB2 | c.2305G>T         | D769Y     | Mut             | UNDETERMINED          | false       |
      | EGFR  | c.2239_2241delTTA | L747del   | Mut             | UNDETERMINED          | false       |
      | EGFR  | c.89T>A           | V30D      | Mut             | UNDETERMINED          | false       |
      | EGFR  | c.2573T>G         | L858R     | Mut             | UNDETERMINED          | false       |
      | EGFR  | c.2155G>A         | G719S     | Mut             | UNDETERMINED          | false       |

    And the Analysis belongs to an order that does not have a final report
    When I generate therapy summary

    Then I should get the following results:
      | drug        | variant_summary                 | response_to_drugs   | setting_name | setting_value | on_label | disease_name      |
      | Afatinib    | KRAS G12C                       | Primary sensitivity | Metastatic   | NCCN          | true     | Colorectal Cancer |
      | <ftt_drug>  | EGFR L858R                      | Primary sensitivity | Metastatic   | FDA           | true     | Colorectal Cancer |
      | Afatinib    | BRAF V600E                      | Primary resistance  | Metastatic   | NCCN          | true     | Colorectal Cancer |
      | Gefitinib   | EGFR Exon 19 Deletion (L747del) | Primary resistance  | Metastatic   | NCCN          | true     | Colorectal Cancer |
      | Panitumumab | EGFR V30D                       | Primary sensitivity | Metastatic   | NCCN          | false    | Lung Cancer       |

    Examples:
      | ftt_drug              | ott_drug               |
      | Crizotinib, Erlotinib | Erlotinib, Crizotinib  |
      | Crizotinib, Erlotinib | Erlotinib, Trastuzumab |
      | Crizotinib, Erlotinib | Crizotinib             |
      | Crizotinib            | Erlotinib, Crizotinib  |


  Scenario: No Therapy for Other Tumor Type when the same drug is triggered For Tumor Type, for an order with multiple diseases
    Given the test regions for the SNV test mode include the following genes: NRAS
    And a RuleSet with the following therapy rules:
      | drug     | disease_type      | response_to_drugs   | in                   | out | metastatic |
      | Afatinib | Melanoma          | Primary sensitivity | KRAS c.34G>T G12C    |     | NCCN       |
      | Afatinib | Colorectal Cancer | Primary sensitivity | BRAF c.1799T>A V600E |     | NCCN       |
      | Afatinib | Lung Cancer       | Primary sensitivity | KRAS c.34G>T G12C    |     | NCCN       |

    And an "Colorectal Cancer, Lung Cancer" Analysis with the following results:
      | gene | g_change  | aa_change | decision_result | confirmation_decision | is_reported |
      | KRAS | c.34G>T   | G12C      | Mut             | UNDETERMINED          | false       |
      | BRAF | c.1799T>A | V600E     | Mut             | UNDETERMINED          | false       |

    And the Analysis belongs to an order that does not have a final report
    When I generate therapy summary

    Then I should get the following results (ordered by on_label):
      | drug     | variant_summary | response_to_drugs   | setting_name | setting_value | on_label | disease_name      |
      | Afatinib | BRAF V600E      | Primary sensitivity | Metastatic   | NCCN          | true     | Colorectal Cancer |
      | Afatinib | KRAS G12C       | Primary sensitivity | Metastatic   | NCCN          | true     | Lung Cancer       |


  Scenario Outline: Generate Therapy without Rolling Up Settings
    Given the test regions for the SNV test mode include the following genes: ERBB2,EGFR
    And a RuleSet with the following therapy rules:
      | drug        | disease_type      | response_to_drugs   | in                                     | metastatic | adjuvant  | primary_treatment |
      | Panitumumab | Colorectal Cancer | Primary resistance  | [KRAS c.34G>T G12C, KRAS c.35G>T G12V] | <source1>  | <source2> |                   |
      | Panitumumab | Colorectal Cancer | Primary sensitivity | ERBB2 Wild Type, EGFR Wild Type        | NCCN       | FDA, NCCN | FDA               |
      | Afatinib    | Lung Cancer       | Primary sensitivity | KRAS c.35G>T G12V                      | FDA, NCCN  |           | FDA               |
      | Gefitinib   | Lung Cancer       | Primary sensitivity | KRAS c.35G>T G12V                      | <source3>  | <source4> | <source5>         |

    And an "Colorectal Cancer" Analysis with the following results:
      | gene | g_change | aa_change | decision_result | confirmation_decision | is_reported |
      | KRAS | c.35G>T  | G12V      | Mut             | UNDETERMINED          | false       |

    And the Analysis belongs to an order that does not have a final report
    And the summary engine is configured without summary roll up
    When I generate therapy summary
    Then I should get the following results:
      | drug        | variant_summary                 | response_to_drugs   | setting_name      | setting_value | on_label | disease_name      |
      | Panitumumab | ERBB2 Wild Type::EGFR Wild Type | Primary sensitivity | Metastatic        | NCCN          | true     | Colorectal Cancer |
      | Panitumumab | ERBB2 Wild Type::EGFR Wild Type | Primary sensitivity | Adjuvant          | FDA, NCCN     | true     | Colorectal Cancer |
      | Panitumumab | ERBB2 Wild Type::EGFR Wild Type | Primary sensitivity | Primary treatment | FDA           | true     | Colorectal Cancer |
      | Panitumumab | KRAS G12V                       | Primary resistance  | Metastatic        | <source1>     | true     | Colorectal Cancer |
      | Panitumumab | KRAS G12V                       | Primary resistance  | Adjuvant          | <source2>     | true     | Colorectal Cancer |
      | Afatinib    | KRAS G12V                       | Primary sensitivity | Metastatic        | FDA, NCCN     | false    | Lung Cancer       |
      | Afatinib    | KRAS G12V                       | Primary sensitivity | Primary treatment | FDA           | false    | Lung Cancer       |
      | Gefitinib   | KRAS G12V                       | Primary sensitivity | <setting_name>    | MCG           | false    | Lung Cancer       |

    Examples:
      | source1 | source2 | source3 | source4 | source5 | setting_name      |
      | FDA     | FDA     | MCG     |         |         | Metastatic        |
      | NCCN    | NCCN    |         | MCG     |         | Adjuvant          |
      | MCG     | MCG     |         |         | MCG     | Primary treatment |
      | FDA     | MCG     | MCG     |         |         | Metastatic        |
      | MCG     | NCCN    | MCG     |         |         | Metastatic        |
      | ASCO    | MCG     | MCG     |         |         | Metastatic        |

  Scenario Outline: Generate Therapy while Rolling Up Settings
    Given the test regions for the SNV test mode include the following genes: ERBB2,EGFR
    And a RuleSet with the following therapy rules:
      | drug        | disease_type      | response_to_drugs   | in                                     | metastatic | adjuvant  | primary_treatment |
      | Panitumumab | Colorectal Cancer | Primary resistance  | [KRAS c.34G>T G12C, KRAS c.35G>T G12V] | NCCN       | NCCN      |                   |
      | Panitumumab | Colorectal Cancer | Primary sensitivity | ERBB2 Wild Type, EGFR Wild Type        | NCCN       | MCG, NCCN | FDA               |
      | Afatinib    | Lung Cancer       | Primary sensitivity | KRAS c.35G>T G12V                      | FDA, NCCN  | FDA, NCCN | FDA               |
      | Gefitinib   | Lung Cancer       | Primary sensitivity | KRAS c.35G>T G12V                      | <source1>  | <source2> | <source3>         |

    And an "Colorectal Cancer" Analysis with the following results:
      | gene | g_change | aa_change | decision_result | confirmation_decision | is_reported |
      | KRAS | c.35G>T  | G12V      | Mut             | UNDETERMINED          | false       |

    And the Analysis belongs to an order that does not have a final report
    When I generate therapy summary
    Then I should get the following results:
      | drug        | variant_summary                 | response_to_drugs   | setting_name         | setting_value | on_label | disease_name      |
      | Panitumumab | ERBB2 Wild Type::EGFR Wild Type | Primary sensitivity | Metastatic           | NCCN          | true     | Colorectal Cancer |
      | Panitumumab | ERBB2 Wild Type::EGFR Wild Type | Primary sensitivity | Adjuvant             | MCG, NCCN     | true     | Colorectal Cancer |
      | Panitumumab | ERBB2 Wild Type::EGFR Wild Type | Primary sensitivity | Primary treatment    | FDA           | true     | Colorectal Cancer |
      | Panitumumab | KRAS G12V                       | Primary resistance  | Metastatic, Adjuvant | NCCN          | true     | Colorectal Cancer |
      | Afatinib    | KRAS G12V                       | Primary sensitivity | Metastatic, Adjuvant | FDA, NCCN     | false    | Lung Cancer       |
      | Afatinib    | KRAS G12V                       | Primary sensitivity | Primary treatment    | FDA           | false    | Lung Cancer       |
      | Gefitinib   | KRAS G12V                       | Primary sensitivity | <setting_name>       | MCG           | false    | Lung Cancer       |

    Examples:
      | source1 | source2 | source3 | setting_name      |
      | MCG     |         |         | Metastatic        |
      |         | MCG     |         | Adjuvant          |
      |         |         | MCG     | Primary treatment |

  Scenario Outline: Generate Therapy Rows in Default Sort Order of For Tumor Type then Other Tumor Type and by Response To Drugs within each
    Given a RuleSet with the following therapy rules:
      | drug        | disease_type      | response_to_drugs | in                    | metastatic |
      | Afatinib    | Colorectal Cancer | <response2>       | ERBB2 c.2305G>T D769Y | FDA, NCCN  |
      | Panitumumab | Colorectal Cancer | <response1>       | KRAS c.34G>T G12C     | NCCN       |
      | Gefitinib   | Lung Cancer       | <response3>       | EGFR c.89T>A V30D     | FDA        |
      | Cetuximab   | Lung Cancer       | <response4>       | EGFR c.89T>A V30D     | FDA        |

    And an "Colorectal Cancer" Analysis with the following results:
      | gene  | g_change  | aa_change | decision_result | confirmation_decision | is_reported |
      | KRAS  | c.34G>T   | G12C      | Mut             | UNDETERMINED          | false       |
      | ERBB2 | c.2305G>T | D769Y     | Mut             | UNDETERMINED          | false       |
      | EGFR  | c.89T>A   | V30D      | Mut             | UNDETERMINED          | false       |

    And the Analysis belongs to an order that does not have a final report
    When I generate therapy summary
    Then I should get the following results:
      | drug        | variant_summary | response_to_drugs | setting_name | setting_value | on_label | disease_name      |
      | Panitumumab | KRAS G12C       | <response1>       | Metastatic   | NCCN          | true     | Colorectal Cancer |
      | Afatinib    | ERBB2 D769Y     | <response2>       | Metastatic   | FDA, NCCN     | true     | Colorectal Cancer |
      | Gefitinib   | EGFR V30D       | <response3>       | Metastatic   | FDA           | false    | Lung Cancer       |
      | Cetuximab   | EGFR V30D       | <response4>       | Metastatic   | FDA           | false    | Lung Cancer       |

    Examples:
      | response1                       | response2                       | response3                     | response4                       |
      | Complete response               | Disease free survival           | Complete response             | Disease free survival           |
      | Disease free survival           | Increase in TTP                 | Disease free survival         | Increase in TTP                 |
      | Increase in TTP                 | Improved PFS                    | Increase in TTP               | Improved PFS                    |
      | Improved PFS                    | Improved OS                     | Improved PFS                  | Improved OS                     |
      | Improved OS                     | Partial response                | Improved OS                   | Partial response                |
      | Partial response                | Stable disease                  | Partial response              | Stable disease                  |
      | Stable disease                  | Clinical response               | Stable disease                | Clinical response               |
      | Clinical response               | CCyR                            | Clinical response             | CCyR                            |
      | CCyR                            | MCyR                            | CCyR                          | MCyR                            |
      | MCyR                            | MMR                             | MCyR                          | MMR                             |
      | MMR                             | MHR                             | MMR                           | MHR                             |
      | MHR                             | Primary sensitivity             | MHR                           | Primary sensitivity             |
      | Primary sensitivity             | Overcomes acquired resistance   | Primary sensitivity           | Overcomes acquired resistance   |
      | Overcomes acquired resistance   | Increased sensitivity           | Overcomes acquired resistance | Increased sensitivity           |
      | Increased sensitivity           | Retains sensitivity             | Increased sensitivity         | Retains sensitivity             |
      | Retains sensitivity             | Evidence of activity            | Retains sensitivity           | Evidence of activity            |
      | Evidence of activity            | Theoretical primary sensitivity | Evidence of activity          | Theoretical primary sensitivity |
      | Theoretical primary sensitivity | Decreased sensitivity           | Complete response             | Evidence of activity            |
      | Decreased sensitivity           | May decrease sensitivity        | Complete response             | Evidence of activity            |
      | May decrease sensitivity        | Reduced MCyR                    | Complete response             | Evidence of activity            |
      | Reduced MCyR                    | Resistance                      | Complete response             | Evidence of activity            |
      | Resistance                      | Primary resistance              | Complete response             | Evidence of activity            |
      | Primary resistance              | Acquired resistance             | Complete response             | Evidence of activity            |
      | Acquired resistance             | Secondary resistance            | Complete response             | Evidence of activity            |
      | Secondary resistance            | Theoretical primary resistance  | Complete response             | Evidence of activity            |
      | Theoretical primary resistance  | Unknown                         | Complete response             | Evidence of activity            |

  Scenario Outline: Generate Therapy Rows in Alternative Sort Order of Response To Drugs Only ignoring tumor type
    Given a RuleSet with the following therapy rules:
      | drug        | disease_type    | response_to_drugs     | in                    | metastatic |
      | Afatinib    | <disease_type1> | Improved PFS          | ERBB2 c.2305G>T D769Y | FDA, NCCN  |
      | Panitumumab | <disease_type2> | Increase in TTP       | KRAS c.34G>T G12C     | NCCN       |
      | Gefitinib   | <disease_type3> | Disease free survival | EGFR c.89T>A V30D     | FDA        |
      | Cetuximab   | <disease_type4> | Complete response     | EGFR c.89T>A V30D     | FDA        |

    And an "Colorectal Cancer" Analysis with the following results:
      | gene  | g_change  | aa_change | decision_result | confirmation_decision | is_reported |
      | KRAS  | c.34G>T   | G12C      | Mut             | UNDETERMINED          | false       |
      | ERBB2 | c.2305G>T | D769Y     | Mut             | UNDETERMINED          | false       |
      | EGFR  | c.89T>A   | V30D      | Mut             | UNDETERMINED          | false       |

    And the Analysis belongs to an order that does not have a final report
    And the summary engine is configured for excluding on label status from sorting
    When I generate therapy summary
    Then I should get the following results:
      | drug        | variant_summary | response_to_drugs     | setting_name | setting_value | on_label    | disease_name    |
      | Cetuximab   | EGFR V30D       | Complete response     | Metastatic   | FDA           | <on_label4> | <disease_type4> |
      | Gefitinib   | EGFR V30D       | Disease free survival | Metastatic   | FDA           | <on_label3> | <disease_type3> |
      | Panitumumab | KRAS G12C       | Increase in TTP       | Metastatic   | NCCN          | <on_label2> | <disease_type2> |
      | Afatinib    | ERBB2 D769Y     | Improved PFS          | Metastatic   | FDA, NCCN     | <on_label1> | <disease_type1> |

    Examples:
      | disease_type1     | disease_type2     | disease_type3     | disease_type4     | on_label1 | on_label2 | on_label3 | on_label4 |
      | Lung Cancer       | Lung Cancer       | Colorectal Cancer | Colorectal Cancer | false     | false     | true      | true      |
      | Colorectal Cancer | Colorectal Cancer | Lung Cancer       | Lung Cancer       | true      | true      | false     | false     |
      | Lung Cancer       | Colorectal Cancer | Lung Cancer       | Colorectal Cancer | false     | true      | false     | true      |
      | Colorectal Cancer | Lung Cancer       | Colorectal Cancer | Lung Cancer       | true      | false     | true      | false     |


  Scenario: Generate Therapy Rows in Alternative Sort Order of Source
    Given a RuleSet with the following therapy rules:
      | drug         | disease_type | response_to_drugs               | in                    | metastatic           |
      | Afatinib     | Lung Cancer  | Complete response               | ERBB2 c.2305G>T D769Y | MCG                  |
      | Panitumumab  | Lung Cancer  | Disease free survival           | KRAS c.34G>T G12C     | ASCO                 |
      | Cetuximab    | Lung Cancer  | Clinical response               | EGFR c.89T>A V30D     | ASCO, MCG            |
      | Erlotinib    | Lung Cancer  | Primary sensitivity             | EGFR c.89T>A V30D     | NCCN                 |
      | Gefitinib    | Lung Cancer  | Increased sensitivity           | EGFR c.89T>A V30D     | NCCN, MCG            |
      | Pembrolizumb | Lung Cancer  | Retains sensitivity             | EGFR c.89T>A V30D     | NCCN, ASCO           |
      | Trastuzumab  | Lung Cancer  | Evidence of activity            | EGFR c.89T>A V30D     | NCCN, ASCO, MCG      |
      | Osimertinib  | Lung Cancer  | Theoretical primary sensitivity | EGFR c.89T>A V30D     | FDA                  |
      | Vemurafenib  | Lung Cancer  | Decreased sensitivity           | EGFR c.89T>A V30D     | FDA, MCG             |
      | Sufitinib    | Lung Cancer  | May decrease sensitivity        | EGFR c.89T>A V30D     | FDA, ASCO            |
      | Cobimetinib  | Lung Cancer  | Reduced MCyR                    | EGFR c.89T>A V30D     | FDA, ASCO, MCG       |
      | Ponatinib    | Lung Cancer  | Resistance                      | EGFR c.89T>A V30D     | FDA, NCCN            |
      | Rituximab    | Lung Cancer  | Primary resistance              | EGFR c.89T>A V30D     | FDA, NCCN, MCG       |
      | Everolimus   | Lung Cancer  | Acquired resistance             | EGFR c.89T>A V30D     | FDA, NCCN, ASCO      |
      | Olaparib     | Lung Cancer  | Secondary resistance            | EGFR c.89T>A V30D     | FDA, NCCN, ASCO, MCG |

    And an "Lung Cancer" Analysis with the following results:
      | gene  | g_change  | aa_change | decision_result | confirmation_decision | is_reported |
      | KRAS  | c.34G>T   | G12C      | Mut             | UNDETERMINED          | false       |
      | ERBB2 | c.2305G>T | D769Y     | Mut             | UNDETERMINED          | false       |
      | EGFR  | c.89T>A   | V30D      | Mut             | UNDETERMINED          | false       |

    And the Analysis belongs to an order that does not have a final report
    And the summary engine is configured for sorting by source
    When I generate therapy summary
    Then I should get the following results:
      | drug         | variant_summary | response_to_drugs               | setting_name | setting_value        |
      | Olaparib     | EGFR V30D       | Secondary resistance            | Metastatic   | FDA, NCCN, ASCO, MCG |
      | Everolimus   | EGFR V30D       | Acquired resistance             | Metastatic   | FDA, NCCN, ASCO      |
      | Rituximab    | EGFR V30D       | Primary resistance              | Metastatic   | FDA, NCCN, MCG       |
      | Ponatinib    | EGFR V30D       | Resistance                      | Metastatic   | FDA, NCCN            |
      | Cobimetinib  | EGFR V30D       | Reduced MCyR                    | Metastatic   | FDA, ASCO, MCG       |
      | Sufitinib    | EGFR V30D       | May decrease sensitivity        | Metastatic   | FDA, ASCO            |
      | Vemurafenib  | EGFR V30D       | Decreased sensitivity           | Metastatic   | FDA, MCG             |
      | Osimertinib  | EGFR V30D       | Theoretical primary sensitivity | Metastatic   | FDA                  |
      | Trastuzumab  | EGFR V30D       | Evidence of activity            | Metastatic   | NCCN, ASCO, MCG      |
      | Pembrolizumb | EGFR V30D       | Retains sensitivity             | Metastatic   | NCCN, ASCO           |
      | Gefitinib    | EGFR V30D       | Increased sensitivity           | Metastatic   | NCCN, MCG            |
      | Erlotinib    | EGFR V30D       | Primary sensitivity             | Metastatic   | NCCN                 |
      | Cetuximab    | EGFR V30D       | Clinical response               | Metastatic   | ASCO, MCG            |
      | Panitumumab  | KRAS G12C       | Disease free survival           | Metastatic   | ASCO                 |
      | Afatinib     | ERBB2 D769Y     | Complete response               | Metastatic   | MCG                  |


#######################################################################################################
################################## RULES WITH ONLY OUT-VARIANTS #######################################
#######################################################################################################
  Scenario Outline: Generate Therapy when Out Variants Not Detected With No In Variants
    Given the test regions for the SNV test mode include the following genes: KRAS,EGFR
    And a RuleSet with the following therapy rules:
      | drug        | disease_type      | response_to_drugs   | out                                                         | metastatic | adjuvant |
      | Panitumumab | Colorectal Cancer | Primary resistance  | KRAS c.35G>T G12V, KRAS c.34G>T G12C, EGFR Exon 19 Deletion | NCCN       | NCCN     |
      | Erlotinib   | Colorectal Cancer | Primary sensitivity | KRAS c.35G>T G12V, KRAS c.34G>T G12C, EGFR Exon 19 Deletion | NCCN       | NCCN     |

    And an "Colorectal Cancer" Analysis for an "SNV" Order with the following results:
      | gene | g_change          | aa_change | decision_result | confirmation_decision | is_reported |
      | KRAS | c.34G>T           | G12C      | <KRAS_decision> | <KRAS_confirmation>   | false       |
      | EGFR | c.2239_2241delTTA | L747del   | <EGFR_decision> | <EGFR_confirmation>   | false       |

    And the Analysis belongs to an order that does not have a final report
    When I generate therapy summary
    Then I should get the following results:
      | drug        | variant_summary                               | response_to_drugs   | setting_name         | setting_value | on_label | disease_name      |
      | Erlotinib   | Relevant alterations not detected: KRAS, EGFR | Primary sensitivity | Metastatic, Adjuvant | NCCN          | true     | Colorectal Cancer |
      | Panitumumab | Relevant alterations not detected: KRAS, EGFR | Primary resistance  | Metastatic, Adjuvant | NCCN          | true     | Colorectal Cancer |

    Examples:
      | KRAS_decision | KRAS_confirmation | EGFR_decision | EGFR_confirmation |
      | NONE          | UNDETERMINED      | NONE          | UNDETERMINED      |
      | ND            | UNDETERMINED      | ND            | UNDETERMINED      |
      | FT            | UNDETERMINED      | FT            | UNDETERMINED      |
      | Confirm       | UNDETERMINED      | Confirm       | UNDETERMINED      |
      | Returned      | UNDETERMINED      | Returned      | UNDETERMINED      |
      | Returned      | NOT_DETECTED      | Returned      | NOT_DETECTED      |
      | Returned      | FAILED_TESTING    | Returned      | FAILED_TESTING    |

  Scenario Outline: No Therapy when Any Out Variant Detected Or Pending With No In Variants
    Given the test regions for the SNV test mode include the following genes: KRAS,EGFR
    And a RuleSet with the following therapy rules:
      | drug        | disease_type      | response_to_drugs  | out                                                         | metastatic | adjuvant |
      | Panitumumab | Colorectal Cancer | Primary resistance | KRAS c.35G>T G12V, KRAS c.34G>T G12C, EGFR Exon 19 Deletion | NCCN       | NCCN     |

    And an "Colorectal Cancer" Analysis for an "SNV" Order with the following results:
      | gene | g_change          | aa_change   | decision_result | confirmation_decision | is_reported |
      | KRAS | <g_change>        | <aa_change> | <KRAS_decision> | <KRAS_confirmation>   | false       |
      | EGFR | c.2239_2241delTTA | L747del     | <EGFR_decision> | <EGFR_confirmation>   | false       |

    And the Analysis belongs to an order that does not have a final report
    When I generate therapy summary
    Then I should get no therapy results

    Examples:
      | g_change | aa_change | KRAS_decision | KRAS_confirmation | EGFR_decision | EGFR_confirmation |
      | c.35G>T  | G12V      | Mut           | UNDETERMINED      | ND            | UNDETERMINED      |
      | c.34G>T  | G12C      | Mut           | UNDETERMINED      | ND            | UNDETERMINED      |
      | c.34G>T  | G12C      | Returned      | MUT               | ND            | UNDETERMINED      |
      | c.34G>T  | G12C      | Pending       | UNDETERMINED      | ND            | UNDETERMINED      |
      | c.34G>T  | G12C      | ND            | UNDETERMINED      | Pending       | UNDETERMINED      |
      | c.34G>T  | G12C      | ND            | UNDETERMINED      | Mut           | UNDETERMINED      |
      | c.34G>T  | G12C      | ND            | UNDETERMINED      | Returned      | MUT               |

  Scenario: For rule with only out variants- match rule if all genes in the panel; no match if none are in the panel
    Given the test regions for the SNV test mode include the following genes: BRAF,EGFR,SMO
    And a RuleSet with the following therapy rules:
      | drug        | disease_type      | response_to_drugs   | in | out                                 | metastatic |
      | Panitumumab | Colorectal Cancer | Primary sensitivity |    | BRAF c.1799T>A V600E                | NCCN       |
      | Panitumumab | Colorectal Cancer | Primary sensitivity |    | KRAS c.35G>T G12V                   | NCCN       |
      | Panitumumab | Colorectal Cancer | Primary sensitivity |    | EGFR Exon 19 Deletion, SMO Mutation | NCCN       |
      | Panitumumab | Colorectal Cancer | Primary sensitivity |    | NRAS Mutation, APC Mutation         | NCCN       |

    And an "Colorectal Cancer" Analysis for an "SNV" Order with the following results:
      | gene | g_change  | aa_change | decision_result | confirmation_decision | is_reported |
      | BRAF | c.1799T>A | V600E     | ND              | UNDETERMINED          | false       |

    And the Analysis belongs to an order that does not have a final report
    When I generate therapy summary
    Then I should get the following results:
      | drug        | variant_summary                              | response_to_drugs   | setting_name | setting_value | on_label | disease_name      |
      | Panitumumab | Relevant alterations not detected: BRAF      | Primary sensitivity | Metastatic   | NCCN          | true     | Colorectal Cancer |
      | Panitumumab | Relevant alterations not detected: EGFR, SMO | Primary sensitivity | Metastatic   | NCCN          | true     | Colorectal Cancer |

  Scenario: For rule with only out variants- match rule if all in the panel; no match if none are in the panel (with reflex)
    Given the test regions for the SNV test mode include the following genes: BRAF,EGFR,SMO,KRAS,NRAS,APC
    And the product uses test regions with the following genes:
      | name | reflex_group |
      | BRAF | 1            |
      | EGFR | 2            |
      | SMO  | 3            |
      | KRAS | 4            |
      | NRAS | 4            |
      | APC  | 5            |

    And the product has reflex enabled
    And it has an SNV Workbench Config with the following tabs and Criteria:
      | tab_name      | criteria      | reflex_groups |
      | BRAF          | reflexgroup:1 | 1             |
      | EGFR          | reflexgroup:2 | 2             |
      | SMO           | reflexgroup:3 | 3             |
      | KRAS and NRAS | reflexgroup:4 | 4             |
      | APC           | reflexgroup:5 | 5             |

    And a RuleSet with the following therapy rules:
      | drug        | disease_type      | response_to_drugs   | in | out                                 | metastatic |
      | Panitumumab | Colorectal Cancer | Primary sensitivity |    | BRAF c.1799T>A V600E                | NCCN       |
      | Panitumumab | Colorectal Cancer | Primary sensitivity |    | KRAS c.35G>T G12V                   | NCCN       |
      | Panitumumab | Colorectal Cancer | Primary sensitivity |    | EGFR Exon 19 Deletion, SMO Mutation | NCCN       |
      | Panitumumab | Colorectal Cancer | Primary sensitivity |    | NRAS Mutation, APC Mutation         | NCCN       |

    And an "Colorectal Cancer" Analysis for an "SNV" Order with the following results:
      | gene | g_change  | aa_change | decision_result | confirmation_decision | tab  | is_reported |
      | BRAF | c.1799T>A | V600E     | ND              | UNDETERMINED          | BRAF | false       |

    And the analysis has the following reflex status:
      | reflex_tabs_open |
      | BRAF::EGFR::SMO  |

    And the Analysis belongs to an order that does not have a final report
    When I generate therapy summary
    Then I should get the following results:
      | drug        | variant_summary                              | response_to_drugs   | setting_name | setting_value | on_label | disease_name      |
      | Panitumumab | Relevant alterations not detected: BRAF      | Primary sensitivity | Metastatic   | NCCN          | true     | Colorectal Cancer |
      | Panitumumab | Relevant alterations not detected: EGFR, SMO | Primary sensitivity | Metastatic   | NCCN          | true     | Colorectal Cancer |

  Scenario Outline: Display rule when it has multiple out variants with some in-panel and some off-panel, but indicate which out-variant genes were not tested
    Given the test regions for the SNV test mode include the following genes: <test_regions>
    And a RuleSet with the following therapy rules:
      | drug        | disease_type      | response_to_drugs   | in | out                                                    | metastatic |
      | Panitumumab | Colorectal Cancer | Primary sensitivity |    | BRAF c.1799T>A V600E, KRAS c.35G>T G12V, PTEN Mutation | NCCN       |

    And an "Colorectal Cancer" Analysis for an "SNV" Order with the following results:
      | gene | g_change  | aa_change | decision_result | confirmation_decision | is_reported |
      | BRAF | c.1799T>A | V600E     | ND              | UNDETERMINED          | false       |

    And the Analysis belongs to an order that does not have a final report
    When I generate therapy summary
    Then I should get the following results:
      | drug        | variant_summary   | response_to_drugs   | setting_name | setting_value | on_label | disease_name      |
      | Panitumumab | <variant_summary> | Primary sensitivity | Metastatic   | NCCN          | true     | Colorectal Cancer |

    Examples:
      | test_regions | variant_summary                                                                                 |
      | BRAF         | Relevant alterations not detected: BRAF, (KRAS *<i>not tested</i>*), (PTEN *<i>not tested</i>*) |
      | KRAS         | Relevant alterations not detected: KRAS, (BRAF *<i>not tested</i>*), (PTEN *<i>not tested</i>*) |
      | PTEN,KRAS    | Relevant alterations not detected: KRAS, PTEN, (BRAF *<i>not tested</i>*)                       |

  Scenario: Display rule when it has multiple out variants with some in-panel and some off-panel, but indicate which out-variant genes were not tested (with reflex)
    Given the test regions for the SNV test mode include the following genes: EGFR,KRAS,PTEN,NRAS,SMO,BRAF
    And the product uses test regions with the following genes:
      | name | reflex_group |
      | KRAS | 1            |
      | PTEN | 2            |
      | NRAS | 3            |
      | BRAF | 3            |

    And the product has reflex enabled
    And it has an SNV Workbench Config with the following tabs and Criteria:
      | tab_name      | criteria      | reflex_groups |
      | KRAS          | reflexgroup:1 | 1             |
      | PTEN          | reflexgroup:2 | 2             |
      | NRAS and BRAF | reflexgroup:3 | 3             |

    And a RuleSet with the following therapy rules:
      | drug        | disease_type      | response_to_drugs   | in | out                                                    | metastatic |
      | Panitumumab | Colorectal Cancer | Primary sensitivity |    | BRAF c.1799T>A V600E, KRAS c.35G>T G12V, PTEN Mutation | NCCN       |

    And an "Colorectal Cancer" Analysis for an "SNV" Order with the following results:
      | gene | g_change  | aa_change | decision_result | confirmation_decision | tab  | is_reported |
      | BRAF | c.1799T>A | V600E     | ND              | UNDETERMINED          | BRAF | false       |

    And the analysis has the following reflex status:
      | reflex_tabs_open    |
      | NRAS and BRAF::KRAS |

    And the Analysis belongs to an order that does not have a final report
    When I generate therapy summary
    Then I should get the following results:
      | drug        | variant_summary                                                           | response_to_drugs   | setting_name | setting_value | on_label | disease_name      |
      | Panitumumab | Relevant alterations not detected: BRAF, KRAS, (PTEN *<i>not tested</i>*) | Primary sensitivity | Metastatic   | NCCN          | true     | Colorectal Cancer |

  Scenario: For rule with only out variants- all genes considered to be on the panel if there are no SNV test regions
    Given the Product has no SNV test regions defined
    And a RuleSet with the following therapy rules:
      | drug        | disease_type      | response_to_drugs   | in | out                                 | metastatic |
      | Panitumumab | Colorectal Cancer | Primary sensitivity |    | KRAS c.35G>T G12V                   | NCCN       |
      | Panitumumab | Colorectal Cancer | Primary sensitivity |    | EGFR Exon 19 Deletion, SMO Mutation | NCCN       |

    And an "Colorectal Cancer" Analysis for an "SNV" Order with the following results:
      | gene | g_change  | aa_change | decision_result | confirmation_decision | is_reported |
      | BRAF | c.1799T>A | V600E     | ND              | UNDETERMINED          | false       |

    And the Analysis belongs to an order that does not have a final report
    When I generate therapy summary
    Then I should get the following results:
      | drug        | variant_summary                              | response_to_drugs   | setting_name | setting_value | on_label | disease_name      |
      | Panitumumab | Relevant alterations not detected: KRAS      | Primary sensitivity | Metastatic   | NCCN          | true     | Colorectal Cancer |
      | Panitumumab | Relevant alterations not detected: EGFR, SMO | Primary sensitivity | Metastatic   | NCCN          | true     | Colorectal Cancer |

  Scenario Outline: For rule with only-outs using SNaPshot- match rule if gene has any non-failed variants; no match if all variants in gene fail
    Given the test regions for the SNV test mode include the following genes: BRAF,KRAS,EGFR,SMO,NRAS,APC
    And a RuleSet with the following therapy rules:
      | drug        | disease_type      | response_to_drugs   | in | out                         | metastatic |
      | Panitumumab | Colorectal Cancer | Primary sensitivity |    | BRAF c.1799T>A V600E        | NCCN       |
      | Panitumumab | Colorectal Cancer | Primary sensitivity |    | KRAS c.35G>T G12V           | NCCN       |
      | Panitumumab | Colorectal Cancer | Primary sensitivity |    | EGFR Mutation, SMO Mutation | NCCN       |
      | Panitumumab | Colorectal Cancer | Primary sensitivity |    | NRAS Mutation, APC Mutation | NCCN       |

    And an "Colorectal Cancer" Analysis for an "SNV" Order with the following results:
      | gene | g_change              | aa_change | decision_result   | confirmation_decision | is_reported | platform |
      | BRAF | c.1799T>A             | V600E     | <decision_result> | UNDETERMINED          | false       | SNaPshot |
      | KRAS | c.34G>T               | G12C      | FT                | UNDETERMINED          | false       | SNaPshot |
      | KRAS | c.182A>T              | Q61L      | FT                | UNDETERMINED          | false       | SNaPshot |
      | EGFR | c.2156G>C             | G719A     | FT                | UNDETERMINED          | false       | SNaPshot |
      | EGFR | c.2582T>A             | L861Q     | ND                | UNDETERMINED          | false       | SNaPshot |
      | NRAS | c.35G>C               | G12A      | ND                | UNDETERMINED          | false       | SNaPshot |
      | APC  | c.4199_4200delCGinsAA | S1400*    | FT                | UNDETERMINED          | false       | SNaPshot |

    And the Analysis belongs to an order that does not have a final report
    When I generate therapy summary
    Then I should get the following results:
      | drug        | variant_summary                                                    | response_to_drugs   | setting_name | setting_value | on_label | disease_name      |
      | Panitumumab | Relevant alterations not detected: BRAF                            | Primary sensitivity | Metastatic   | NCCN          | true     | Colorectal Cancer |
      | Panitumumab | Relevant alterations not detected: EGFR, SMO                       | Primary sensitivity | Metastatic   | NCCN          | true     | Colorectal Cancer |
      | Panitumumab | Relevant alterations not detected: NRAS, (APC *<i>not tested</i>*) | Primary sensitivity | Metastatic   | NCCN          | true     | Colorectal Cancer |

    Examples:
      | decision_result       |
      | ND                    |
      | NONE                  |
      | Confirm               |
      | NOT_REVIEWED          |
      | DETECTED_NOT_REPORTED |
      | Returned              |

  Scenario: SNaPshot failed testing and out-only-rules, when not all genes are on the panel
    Given the test regions for the SNV test mode include the following genes: EGFR,KRAS,NRAS
    And a RuleSet with the following therapy rules:
      | drug        | disease_type      | response_to_drugs   | in | out                                                    | metastatic |
      | Panitumumab | Colorectal Cancer | Primary sensitivity |    | EGFR c.2156G>C G719A, KRAS c.35G>T G12V, PTEN Mutation | NCCN       |
      | Panitumumab | Colorectal Cancer | Primary sensitivity |    | NRAS c.35G>C G12A, SMO Mutation                        | NCCN       |

    And an "Colorectal Cancer" Analysis for an "SNV" Order with the following results:
      | gene | g_change | aa_change | decision_result | confirmation_decision | is_reported | platform |
      | KRAS | c.34G>T  | G12C      | FT              | UNDETERMINED          | false       | SNaPshot |
      | KRAS | c.182A>T | Q61L      | FT              | UNDETERMINED          | false       | SNaPshot |
      | NRAS | c.35G>C  | G12A      | FT              | UNDETERMINED          | false       | SNaPshot |

    And the Analysis belongs to an order that does not have a final report
    When I generate therapy summary
    Then I should get the following results:
      | drug        | variant_summary                                                                                 | response_to_drugs   | setting_name | setting_value | on_label | disease_name      |
      | Panitumumab | Relevant alterations not detected: EGFR, (KRAS *<i>not tested</i>*), (PTEN *<i>not tested</i>*) | Primary sensitivity | Metastatic   | NCCN          | true     | Colorectal Cancer |


#######################################################################################################
#######################################################################################################
#######################################################################################################



################################################################################
########################### ADDENDUMS AND AMENDMENTS ###########################
################################################################################

  Scenario Outline: No Therapy when Pending Variant Could Cause Suppression Later Because Of Combo Therapy
    Given the test regions for the SNV test mode include the following genes: SMO
    And a RuleSet with the following therapy rules:
      | drug        | disease_type      | response_to_drugs   | in               | metastatic |
      | Panitumumab | Colorectal Cancer | Primary sensitivity | <rule1>          | NCCN       |
      | Panitumumab | Colorectal Cancer | Primary sensitivity | <rule1>, <rule2> | NCCN       |

    And an "Colorectal Cancer" Analysis with the following results:
      | gene    | g_change | aa_change | decision_result | confirmation_decision | is_reported |
      | <gene1> | <c.1>    | <aa1>     | Mut             | UNDETERMINED          | false       |
      | <gene2> | <c.2>    | <aa2>     | Pending         | UNDETERMINED          | false       |

    And the Analysis belongs to an order that does not have a final report
    When I generate therapy summary
    Then I should get no therapy results

    Examples:
      | rule1                 | gene1 | c.1               | aa1     | rule2                 | gene2 | c.2                | aa2        |
      | KRAS c.34G>T G12C     | KRAS  | c.34G>T           | G12C    | EGFR c.89T>A V30D     | EGFR  | c.89T>A            | V30D       |
      | EGFR Exon 19 Deletion | EGFR  | c.2239_2241delTTA | L747del | KRAS c.34G>T G12C     | KRAS  | c.34G>T            | G12C       |
      | EGFR Exon 19 Deletion | EGFR  | c.2239_2241delTTA | L747del | SMO Wild Type         | SMO   | c.118_123delGGGCCT | G40_P41del |
      | SMO Wild Type         | KRAS  | c.34G>T           | G12C    | EGFR Exon 19 Deletion | EGFR  | c.2239_2241delTTA  | L747del    |

  Scenario Outline: Generate Therapy Rows For Addendum Report
    Given the test regions for the SNV test mode include the following genes: SMAD4,KIT
    And a RuleSet with the following therapy rules:
      | drug        | disease_type      | response_to_drugs   | in                                     | metastatic |
      | Panitumumab | Colorectal Cancer | Primary sensitivity | KRAS c.34G>T G12C                      | NCCN       |
      | Panitumumab | Colorectal Cancer | Primary sensitivity | KRAS c.34G>T G12C, EGFR c.89T>A V30D   | NCCN       |
      | Afatinib    | Colorectal Cancer | Primary sensitivity | BRAF c.1799T>A V600E                   | NCCN       |
      | Gefitinib   | Colorectal Cancer | Primary sensitivity | SMO c.118_123delGGGCCT G40_P41del      | NCCN       |
      | Gefitinib   | Colorectal Cancer | Primary sensitivity | SMAD4 Wild Type                        | NCCN       |
      | Gefitinib   | Colorectal Cancer | Primary sensitivity | SMAD4 Wild Type, EGFR Exon 19 Deletion | NCCN       |
      | Gefitinib   | Colorectal Cancer | Primary sensitivity | ERBB2 c.2524G>A V842I                  | NCCN       |
      | Gefitinib   | Colorectal Cancer | Primary sensitivity | ERBB2 c.2524G>A V842I, KIT Wild Type   | NCCN       |

    And an "Colorectal Cancer" Analysis with the following results:
      | gene  | g_change           | aa_change  | decision_result | confirmation_decision | is_reported |
      | KRAS  | c.34G>T            | G12C       | Mut             | UNDETERMINED          | true        |
      | EGFR  | c.89T>A            | V30D       | Returned        | MUT                   | false       |
      | BRAF  | c.1799T>A          | V600E      | Mut             | UNDETERMINED          | true        |
      | SMO   | c.118_123delGGGCCT | G40_P41del | Returned        | MUT                   | false       |
      | EGFR  | c.2239_2241delTTA  | L747del    | Returned        | MUT                   | false       |
      | ERBB2 | c.2524G>A          | V842I      | Mut             | UNDETERMINED          | true        |
      | KIT   | c.1679_1681delTTG  | V560del    | Returned        | NOT_DETECTED          | false       |

    And the Analysis belongs to an order that does have a final report
    And the Product is set up so that the addendum report <does_or_does_not> replace
    When I generate therapy summary
    Then I should get the following results:
      | drug        | variant_summary                                  | response_to_drugs   | setting_name | setting_value | on_label | disease_name      |
      | Afatinib    | BRAF V600E                                       | Primary sensitivity | Metastatic   | NCCN          | true     | Colorectal Cancer |
      | Gefitinib   | SMO G40_P41del                                   | Primary sensitivity | Metastatic   | NCCN          | true     | Colorectal Cancer |
      | Gefitinib   | SMAD4 Wild Type::EGFR Exon 19 Deletion (L747del) | Primary sensitivity | Metastatic   | NCCN          | true     | Colorectal Cancer |
      | Gefitinib   | ERBB2 V842I::KIT Wild Type                       | Primary sensitivity | Metastatic   | NCCN          | true     | Colorectal Cancer |
      | Panitumumab | KRAS G12C::EGFR V30D                             | Primary sensitivity | Metastatic   | NCCN          | true     | Colorectal Cancer |

    Examples:
      | does_or_does_not |
      | does             |
      | does not         |


  Scenario Outline: Generate Therapy For Addendum With Variants Still Pending
    Given a RuleSet with the following therapy rules:
      | drug        | disease_type      | response_to_drugs   | in                                                   | metastatic |
      | Panitumumab | Colorectal Cancer | Primary sensitivity | KRAS c.34G>T G12C                                    | NCCN       |
      | Panitumumab | Colorectal Cancer | Primary sensitivity | KRAS c.34G>T G12C, EGFR c.89T>A V30D                 | NCCN       |
      | Gefitinib   | Colorectal Cancer | Primary sensitivity | ERBB2 c.2305G>C D769H                                | NCCN       |
      | Gefitinib   | Colorectal Cancer | Primary sensitivity | ERBB2 c.2305G>C D769H, KIT c.1679_1681delTTG V560del | NCCN       |
      | Afatinib    | Lung Cancer       | Primary sensitivity | BRAF c.1799T>A V600E                                 | NCCN       |

    And an "Colorectal Cancer" Analysis with the following results:
      | gene  | g_change          | aa_change | decision_result | confirmation_decision | is_reported |
      | KRAS  | c.34G>T           | G12C      | Mut             | UNDETERMINED          | true        |
      | EGFR  | c.89T>A           | V30D      | Returned        | MUT                   | false       |
      | BRAF  | c.1799T>A         | V600E     | Mut             | UNDETERMINED          | true        |
      | ERBB2 | c.2305G>C         | D769H     | Mut             | UNDETERMINED          | true        |
      | KIT   | c.1679_1681delTTG | V560del   | Pending         | UNDETERMINED          | false       |

    And the Analysis belongs to an order that does have a final report
    And the Product is set up so that the addendum report <does_or_does_not> replace
    When I generate therapy summary
    Then I should get the following results:
      | drug        | variant_summary      | response_to_drugs   | setting_name | setting_value | on_label | disease_name      |
      | Panitumumab | KRAS G12C::EGFR V30D | Primary sensitivity | Metastatic   | NCCN          | true     | Colorectal Cancer |
      | Afatinib    | BRAF V600E           | Primary sensitivity | Metastatic   | NCCN          | false    | Lung Cancer       |

    Examples:
      | does_or_does_not |
      | does             |
      | does not         |

  Scenario: Generate All Therapies for Amendment
    Given the test regions for the SNV test mode include the following genes: SMAD4,KIT
    And a RuleSet with the following therapy rules:
      | drug        | disease_type      | response_to_drugs   | in                                     | metastatic |
      | Panitumumab | Colorectal Cancer | Primary sensitivity | KRAS c.34G>T G12C                      | NCCN       |
      | Panitumumab | Colorectal Cancer | Primary sensitivity | KRAS c.34G>T G12C, EGFR c.89T>A V30D   | NCCN       |
      | Afatinib    | Colorectal Cancer | Primary sensitivity | BRAF c.1799T>A V600E                   | NCCN       |
      | Gefitinib   | Colorectal Cancer | Primary sensitivity | SMO c.118_123delGGGCCT G40_P41del      | NCCN       |
      | Gefitinib   | Colorectal Cancer | Primary sensitivity | SMAD4 Wild Type                        | NCCN       |
      | Gefitinib   | Colorectal Cancer | Primary sensitivity | SMAD4 Wild Type, EGFR Exon 19 Deletion | NCCN       |
      | Gefitinib   | Colorectal Cancer | Primary sensitivity | ERBB2 c.2524G>A V842I                  | NCCN       |
      | Gefitinib   | Colorectal Cancer | Primary sensitivity | ERBB2 c.2524G>A V842I, KIT Wild Type   | NCCN       |

    And an "Colorectal Cancer" Analysis with the following results:
      | gene  | g_change           | aa_change  | decision_result | confirmation_decision | is_reported |
      | KRAS  | c.34G>T            | G12C       | Mut             | UNDETERMINED          | true        |
      | EGFR  | c.89T>A            | V30D       | Returned        | MUT                   | true        |
      | BRAF  | c.1799T>A          | V600E      | Mut             | UNDETERMINED          | true        |
      | SMO   | c.118_123delGGGCCT | G40_P41del | Returned        | MUT                   | true        |
      | EGFR  | c.2239_2241delTTA  | L747del    | Returned        | MUT                   | true        |
      | ERBB2 | c.2524G>A          | V842I      | Mut             | UNDETERMINED          | true        |
      | KIT   | c.1679_1681delTTG  | V560del    | Returned        | NOT_DETECTED          | true        |

    And the Analysis belongs to an order that does have a final report
    And the Analysis is a Workbench Error Amendment
    And the Product is set up so that the addendum report does not replace
    When I generate therapy summary
    Then I should get the following results:
      | drug        | variant_summary                                  | response_to_drugs   | setting_name | setting_value | on_label | disease_name      |
      | Afatinib    | BRAF V600E                                       | Primary sensitivity | Metastatic   | NCCN          | true     | Colorectal Cancer |
      | Gefitinib   | SMO G40_P41del                                   | Primary sensitivity | Metastatic   | NCCN          | true     | Colorectal Cancer |
      | Gefitinib   | SMAD4 Wild Type::EGFR Exon 19 Deletion (L747del) | Primary sensitivity | Metastatic   | NCCN          | true     | Colorectal Cancer |
      | Gefitinib   | ERBB2 V842I::KIT Wild Type                       | Primary sensitivity | Metastatic   | NCCN          | true     | Colorectal Cancer |
      | Panitumumab | KRAS G12C::EGFR V30D                             | Primary sensitivity | Metastatic   | NCCN          | true     | Colorectal Cancer |

################################################################################
################################################################################
################################################################################


  Scenario: Generate Therapy for SNaPshot variant
    Given the test regions for the SNV test mode include the following genes: BRAF
    And a Product with a SNaPshot configuration that has the following SNaPshot hashes:
      | name                | value                     |
      | 150066729094TGGAGAD |                           |
      | 170037880261G_T     |                           |
      | 070140453136A_T     | Fancy BRAF Mut Name       |
      | 100089717716I_TTA   | Fancy PTEN Insertion Name |

    And a RuleSet with the following therapy rules:
      | drug        | disease_type      | response_to_drugs   | in                    | metastatic |
      | Panitumumab | Colorectal Cancer | Primary sensitivity | PTEN Insertion        | FDA        |
      | Afatinib    | Colorectal Cancer | Primary sensitivity | ERBB2 c.2305G>T D769Y | NCCN       |
      | Gefitinib   | Colorectal Cancer | Primary sensitivity | BRAF c.1799T>A V600E  | ASCO       |
      | Imatinib    | Colorectal Cancer | Primary sensitivity | MAP2K1 Deletion       | MCG        |
      | Erlotinib   | Colorectal Cancer | Primary sensitivity | BRAF Wild Type        | FDA        |

    And an "Colorectal Cancer" Analysis with the following results:
      | mutation_hash       | gene   | g_change           | aa_change    | decision_result | confirmation_decision | is_reported |
      | 100089717716I_TTA   | PTEN   | c.739_741dupTTA    | L247dup      | Mut             | UNDETERMINED          | false       |
      | 170037880261G_T     | ERBB2  | c.2305G>T          | D769Y        | Mut             | UNDETERMINED          | false       |
      | 070140453136A_T     | BRAF   | c.1799T>A          | V600E        | Mut             | UNDETERMINED          | false       |
      | 150066729094TGGAGAD | MAP2K1 | c.303_308delGGAGAT | E102_I103del | Mut             | UNDETERMINED          | false       |

    And the Analysis belongs to an order that does not have a final report
    When I generate therapy summary
    Then I should get the following results:
      | drug        | variant_summary                | response_to_drugs   | setting_name | setting_value | on_label | disease_name      |
      | Afatinib    | ERBB2 D769Y                    | Primary sensitivity | Metastatic   | NCCN          | true     | Colorectal Cancer |
      | Gefitinib   | Fancy BRAF Mut Name            | Primary sensitivity | Metastatic   | ASCO          | true     | Colorectal Cancer |
      | Imatinib    | MAP2K1 Deletion (E102_I103del) | Primary sensitivity | Metastatic   | MCG           | true     | Colorectal Cancer |
      | Panitumumab | Fancy PTEN Insertion Name      | Primary sensitivity | Metastatic   | FDA           | true     | Colorectal Cancer |

  Scenario: Generate Therapy With p. Output
    Given the test regions for the SNV test mode include the following genes: NRAS
    And a RuleSet with the following therapy rules:
      | drug        | disease_type      | response_to_drugs   | in                    | metastatic | adjuvant |
      | Panitumumab | Colorectal Cancer | Primary sensitivity | KRAS c.35G>T G12V     | NCCN       | NCCN     |
      | Afatinib    | Colorectal Cancer | Primary sensitivity | EGFR Exon 19 Deletion | NCCN       | NCCN     |
      | Gefitinib   | Colorectal Cancer | Primary sensitivity | NRAS Wild Type        | NCCN       | NCCN     |

    And an "Colorectal Cancer" Analysis with the following results:
      | gene | g_change          | aa_change | decision_result | confirmation_decision | is_reported |
      | KRAS | c.35G>T           | G12V      | Mut             | UNDETERMINED          | false       |
      | EGFR | c.2239_2241delTTA | L747del   | Mut             | UNDETERMINED          | false       |

    And the Analysis belongs to an order that does not have a final report
    And the summary engine is configured for pdot format
    When I generate therapy summary
    Then I should get the following results:
      | drug        | variant_summary                   | response_to_drugs   | setting_name         | setting_value | on_label | disease_name      |
      | Afatinib    | EGFR Exon 19 Deletion (p.L747del) | Primary sensitivity | Metastatic, Adjuvant | NCCN          | true     | Colorectal Cancer |
      | Gefitinib   | NRAS Wild Type                    | Primary sensitivity | Metastatic, Adjuvant | NCCN          | true     | Colorectal Cancer |
      | Panitumumab | KRAS p.G12V                       | Primary sensitivity | Metastatic, Adjuvant | NCCN          | true     | Colorectal Cancer |

  Scenario: Indicate whether each therapy is approved for the patient's tumor type
    Given the test regions for the SNV test mode include the following genes: KRAS
    And a RuleSet with the following therapy rules:
      | drug        | disease_type      | response_to_drugs   | in                    | metastatic |
      | Panitumumab | Lung Cancer       | Primary sensitivity | PTEN Insertion        | FDA        |
      | Afatinib    | Lung Cancer       | Primary sensitivity | ERBB2 c.2305G>T D769Y | NCCN       |
      | Gefitinib   | Colorectal Cancer | Primary sensitivity | BRAF c.1799T>A V600E  | ASCO       |
      | Imatinib    | Colorectal Cancer | Primary sensitivity | MAP2K1 Deletion       | MCG        |
      | Erlotinib   | Colorectal Cancer | Primary sensitivity | KRAS Wild Type        | FDA        |
      | Sunitinib   | Colorectal Cancer | Primary sensitivity | KRAS Wild Type        | FDA        |

    And an "Colorectal Cancer" Analysis with the following results:
      | gene   | g_change           | aa_change    | decision_result | confirmation_decision | is_reported |
      | PTEN   | c.739_741dupTTA    | L247dup      | Mut             | UNDETERMINED          | false       |
      | ERBB2  | c.2305G>T          | D769Y        | Mut             | UNDETERMINED          | false       |
      | BRAF   | c.1799T>A          | V600E        | Mut             | UNDETERMINED          | false       |
      | MAP2K1 | c.303_308delGGAGAT | E102_I103del | Mut             | UNDETERMINED          | false       |

    And the following Drugs objects:
      | name        | fda_approved                      |
      | Panitumumab | Colorectal Cancer                 |
      | Afatinib    | Lung Cancer                       |
      | Gefitinib   | Thyroid Cancer, Colorectal Cancer |
      | Erlotinib   | Colorectal Cancer                 |
      | Sunitinib   | Thyroid Cancer, Breast Cancer     |

    And the Analysis belongs to an order that does not have a final report
    When I generate therapy summary
    Then I should get the following results:
      | drug        | variant_summary                | response_to_drugs   | setting_name | setting_value | on_label | disease_name      | fda_approved/Erlotinib | fda_approved/Gefitinib | fda_approved/Imatinib | fda_approved/Sunitinib | fda_approved/Afatinib | fda_approved/Panitumumab |
      | Erlotinib   | KRAS Wild Type                 | Primary sensitivity | Metastatic   | FDA           | true     | Colorectal Cancer | true                   |                        |                       |                        |                       |                          |
      | Gefitinib   | BRAF V600E                     | Primary sensitivity | Metastatic   | ASCO          | true     | Colorectal Cancer |                        | true                   |                       |                        |                       |                          |
      | Imatinib    | MAP2K1 Deletion (E102_I103del) | Primary sensitivity | Metastatic   | MCG           | true     | Colorectal Cancer |                        |                        | false                 |                        |                       |                          |
      | Sunitinib   | KRAS Wild Type                 | Primary sensitivity | Metastatic   | FDA           | true     | Colorectal Cancer |                        |                        |                       | false                  |                       |                          |
      | Afatinib    | ERBB2 D769Y                    | Primary sensitivity | Metastatic   | NCCN          | false    | Lung Cancer       |                        |                        |                       |                        | false                 |                          |
      | Panitumumab | PTEN Insertion (L247dup)       | Primary sensitivity | Metastatic   | FDA           | false    | Lung Cancer       |                        |                        |                       |                        |                       | true                     |

  Scenario: Generate therapy with multiple response to drug values
    Given a RuleSet with the following therapy rules:
      | drug      | disease_type | response_to_drugs                       | in                                      | metastatic |
      | Erlotinib | Lung Cancer  | Primary resistance, Acquired resistance | EGFR c.2155G>A G719S, KRAS c.35G>T G12V | NCCN       |

    And an "Lung Cancer" Analysis with the following results:
      | gene | g_change  | aa_change | decision_result | confirmation_decision | is_reported |
      | KRAS | c.35G>T   | G12V      | Mut             | UNDETERMINED          | false       |
      | EGFR | c.2155G>A | G719S     | Mut             | UNDETERMINED          | false       |

    And the Analysis belongs to an order that does not have a final report
    When I generate therapy summary
    Then I should get the following results:
      | drug      | variant_summary       | response_to_drugs                       | setting_name | setting_value | on_label | disease_name |
      | Erlotinib | EGFR G719S::KRAS G12V | Primary resistance, Acquired resistance | Metastatic   | NCCN          | true     | Lung Cancer  |


  Scenario: Generate therapy when variant matches gene and amino acid change, but not hash or nucleotide change
    Given a RuleSet with the following therapy rules:
      | drug        | disease_type      | response_to_drugs  | in                 | metastatic |
      | Panitumumab | Colorectal Cancer | Primary resistance | KRAS c.181C>A Q61K | NCCN       |

    And an "Colorectal Cancer" Analysis with the following results:
      | gene | g_change       | aa_change | decision_result | confirmation_decision | is_reported |
      | KRAS | c.180_181TC>AA | Q61K      | Mut             | UNDETERMINED          | false       |

    And the Analysis belongs to an order that does not have a final report
    When I generate therapy summary
    Then I should get the following results:
      | drug        | variant_summary | response_to_drugs  | setting_name | setting_value | on_label | disease_name      |
      | Panitumumab | KRAS Q61K       | Primary resistance | Metastatic   | NCCN          | true     | Colorectal Cancer |

  Scenario: Return variant hashes that triggered therapy rows
    Given a RuleSet with the following therapy rules:
      | drug        | disease_type      | response_to_drugs   | in                                            | out               | metastatic |
      | Afatinib    | Lung Cancer       | Primary sensitivity | [EGFR c.2155G>A G719S, ERBB2 c.2305G>T D769Y] | KRAS c.35G>T G12V | FDA        |
      | Erlotinib   | Lung Cancer       | Acquired resistance | EGFR c.2369C>T T790M, EGFR c.2155G>A G719S    |                   | FDA        |
      | Afatinib    | Lung Cancer       | Primary sensitivity | MAP2K1 Deletion                               |                   | FDA        |
      | Panitumumab | Colorectal Cancer | Primary sensitivity | KRAS c.181C>A Q61K                            |                   | NCCN       |
      | Panitumumab | Thyroid Cancer    | Primary sensitivity | ERBB2 Codon 755 Missense                      |                   | NCCN       |

    And an "Lung Cancer" Analysis for an "SNV" Order with the following results:
      | hash                | gene   | g_change            | aa_change    | decision_result | confirmation_decision | is_reported |
      | 070055241707G_A     | EGFR   | c.2155G>A           | G719S        | Mut             | UNDETERMINED          | false       |
      | 070055249071C_T     | EGFR   | c.2369C>T           | T790M        | Mut             | UNDETERMINED          | false       |
      | 150066729094TGGAGAD | MAP2K1 | c.303_308delGGAGAT  | E102_I103del | Mut             | UNDETERMINED          | false       |
      | 120025380277GA_TT   | KRAS   | c.180_181delTCinsAA | Q61K         | Mut             | UNDETERMINED          | false       |
      | 170037880220T_C     | ERBB2  | c.2264T>C           | L755S        | Mut             | UNDETERMINED          | false       |

    And the Analysis belongs to an order that does not have a final report
    When I generate therapy summary
    Then I should get the following results:
      | drug        | variant_summary                  | response_to_drugs   | setting_name | setting_value | on_label | disease_name      |
      | Afatinib    | EGFR G719S                       | Primary sensitivity | Metastatic   | FDA           | true     | Lung Cancer       |
      | Afatinib    | MAP2K1 Deletion (E102_I103del)   | Primary sensitivity | Metastatic   | FDA           | true     | Lung Cancer       |
      | Erlotinib   | EGFR T790M::EGFR G719S           | Acquired resistance | Metastatic   | FDA           | true     | Lung Cancer       |
      | Panitumumab | KRAS Q61K                        | Primary sensitivity | Metastatic   | NCCN          | false    | Colorectal Cancer |
      | Panitumumab | ERBB2 Codon 755 Missense (L755S) | Primary sensitivity | Metastatic   | NCCN          | false    | Thyroid Cancer    |

    And I should get the following therapy hashes:
      | hash                | on_label | wild_type | test_mode |
      | 070055241707G_A     | true     | false     | SNV       |
      | 070055249071C_T     | true     | false     | SNV       |
      | 150066729094TGGAGAD | true     | false     | SNV       |
      | 120025380277GA_TT   | false    | false     | SNV       |
      | 170037880220T_C     | false    | false     | SNV       |

  Scenario: Return wild-type hashes that triggered therapy rows
    Given the test regions for the SNV test mode include the following genes: KIT,ERBB2
    And a RuleSet with the following therapy rules:
      | drug     | disease_type | response_to_drugs   | in                                           | metastatic |
      | Imatinib | GIST         | Primary resistance  | KIT Wild Type                                | FDA        |
      | Afatinib | GIST         | Primary sensitivity | ERBB2 Exon 1 Wild Type, EGFR c.2155G>A G719S | FDA        |

    And an "GIST" Analysis with the following results:
      | hash              | gene | g_change            | aa_change | decision_result | confirmation_decision | is_reported |
      | 070055241707G_A   | EGFR | c.2155G>A           | G719S     | Mut             | UNDETERMINED          | false       |
      | 120025380277GA_TT | KRAS | c.180_181delTCinsAA | Q61K      | Mut             | UNDETERMINED          | false       |

    And the Analysis belongs to an order that does not have a final report
    When I generate therapy summary
    Then I should get the following results:
      | drug     | variant_summary                    | response_to_drugs   | setting_name | setting_value | on_label | disease_name |
      | Afatinib | ERBB2 Exon 1 Wild Type::EGFR G719S | Primary sensitivity | Metastatic   | FDA           | true     | GIST         |
      | Imatinib | KIT Wild Type                      | Primary resistance  | Metastatic   | FDA           | true     | GIST         |

    And I should get the following therapy hashes:
      | hash              | on_label | wild_type | test_mode |
      | 070055241707G_A   | true     | false     | SNV       |
      | KIT:Wild Type     | true     | true      | SNV       |
      | ERBB2:1:Wild Type | true     | true      | SNV       |

  Scenario: No variant hashes when variant doesn't trigger therapy or is an out variant
    Given the test regions for the SNV test mode include the following genes: EGFR,BRAF
    And a RuleSet with the following therapy rules:
      | drug        | disease_type      | response_to_drugs   | in              | out                  | metastatic |
      | Panitumumab | Colorectal Cancer | Primary resistance  |                 | EGFR c.2155G>A G719S | NCCN       |
      | Afatinib    | Colorectal Cancer | Primary sensitivity | EGFR Wild Type  |                      | NCCN       |
      | Erlotinib   | Lung Cancer       | Primary sensitivity | BRAF Wild Type  |                      | NCCN       |
      | Gefitinib   | Lung Cancer       | Primary resistance  | MAP2K1 Deletion |                      | NCCN       |

    And an "Colorectal Cancer" Analysis for an "SNV+CTX" Order with the following results:
      | hash                | gene   | g_change           | aa_change    | decision_result | confirmation_decision | is_reported |
      | 070055241707G_A     | EGFR   | c.2155G>A          | G719S        | Mut             | UNDETERMINED          | false       |
      | 070055249071C_T     | EGFR   | c.2369C>T          | T790M        | Mut             | UNDETERMINED          | false       |
      | 150066729094TGGAGAD | MAP2K1 | c.303_308delGGAGAT | E102_I103del | Mut             | UNDETERMINED          | false       |

    And the Analysis belongs to an order that does not have a final report
    When I generate therapy summary
    Then I should get no therapy results
    And I should no therapy hashes

  Scenario: Generate therapy with multiple drugs
    Given a RuleSet with the following therapy rules:
      | drug                            | disease_type | response_to_drugs  | in                                      | metastatic |
      | Afatinib, Erlotinib             | Lung Cancer  | Primary resistance | EGFR c.2155G>A G719S, KRAS c.35G>T G12V | NCCN       |
      | Afatinib, Crizotinib, Erlotinib | Lung Cancer  | Primary resistance | EGFR c.2155G>A G719S, KRAS c.35G>T G12V | NCCN       |

    And an "Lung Cancer" Analysis with the following results:
      | gene | g_change  | aa_change | decision_result | confirmation_decision | is_reported |
      | KRAS | c.35G>T   | G12V      | Mut             | UNDETERMINED          | false       |
      | EGFR | c.2155G>A | G719S     | Mut             | UNDETERMINED          | false       |

    And the following Drugs objects:
      | name       | fda_approved      | classes                                 |
      | Afatinib   | Lung Cancer       | Immunotherapies, Therapeutic Antibodies |
      | Erlotinib  | Colorectal Cancer | Kinase Inhibitors                       |
      | Crizotinib | Lung Cancer       | Kinase Inhibitors                       |

    And the Analysis belongs to an order that does not have a final report
    When I generate therapy summary
    Then I should get the following results:
      | drug                            | variant_summary       | response_to_drugs  | setting_name | setting_value | on_label | disease_name | fda_approved/Afatinib | fda_approved/Erlotinib | fda_approved/Crizotinib | drug_class/Afatinib                     | drug_class/Erlotinib | drug_class/Crizotinib |
      | Afatinib, Crizotinib, Erlotinib | EGFR G719S::KRAS G12V | Primary resistance | Metastatic   | NCCN          | true     | Lung Cancer  | true                  | false                  | true                    | Immunotherapies, Therapeutic Antibodies | Kinase Inhibitors    | Kinase Inhibitors     |
      | Afatinib, Erlotinib             | EGFR G719S::KRAS G12V | Primary resistance | Metastatic   | NCCN          | true     | Lung Cancer  | true                  | false                  |                         | Immunotherapies, Therapeutic Antibodies | Kinase Inhibitors    |                       |

#######################################################################################################
##################################### GENE VARIANT MODIFIERS ##########################################
#######################################################################################################

  Scenario Outline: Generate therapy for variants with gene variant modifiers when rule specifies the related alteration concept
    Given the classification config has the following gene_variant_modifiers:
      | value                    |
      | FLT3_ITD                 |
      | CEBPA_BIALLELIC_MUTATION |
      | MET_EXON_14_SKIPPING     |

    And the value of has_nonexonic_variants is true
    And a RuleSet with the following therapy rules:
      | drug      | disease_type           | response_to_drugs   | in                       | out | refractory |
      | Sorafenib | Acute Myeloid Leukemia | Primary sensitivity | FLT3 ITD                 |     | NCCN       |
      | Afatinib  | Acute Myeloid Leukemia | Primary sensitivity | MET Exon 14 Skipping     |     | NCCN       |
      | Erlotinib | Acute Myeloid Leukemia | Primary sensitivity | CEBPA Biallelic Mutation |     | NCCN       |

    And an "Acute Myeloid Leukemia" Analysis with the following results:
      | gene  | g_change   | aa_change   | decision_result | is_reported | mutation_type           | classification | gene_variant_modifier_values | hash_override   |
      | FLT3  | <g_change> | <aa_change> | MUT             | false       | <mut_type>              | Uncertain      | FLT3_ITD                     | <hash_override> |
      | MET   | c.3029C>T  | T1010I      | MUT             | false       | Substitution - Missense | Uncertain      | MET_EXON_14_SKIPPING         |                 |
      | CEBPA | c.940G>A   | V314M       | MUT             | false       | Substitution - Missense | Uncertain      | CEBPA_BIALLELIC_MUTATION     |                 |

    When I generate therapy summary
    Then I should get the following results:
      | drug      | variant_summary          | response_to_drugs   | setting_name | setting_value | on_label | disease_name           |
      | Afatinib  | MET Exon 14 Skipping     | Primary sensitivity | Refractory   | NCCN          | true     | Acute Myeloid Leukemia |
      | Erlotinib | CEBPA Biallelic Mutation | Primary sensitivity | Refractory   | NCCN          | true     | Acute Myeloid Leukemia |
      | Sorafenib | FLT3 ITD                 | Primary sensitivity | Refractory   | NCCN          | true     | Acute Myeloid Leukemia |

    Examples:
      | g_change                                              | aa_change    | mut_type                |
      | c.1777_1815dupGATTTCAGAGAATATGAATATGATCTCAAATGGGAGTTT | D593_F605dup | Insertion - In Frame    |
      | c.1829_1830insGCCT                                    | E611Pfs*     | Insertion - Frameshift  |
      | c.1830A>T                                             | L610F        | Substitution - Missense |

  Scenario: Generate therapy for non-coding variants with gene variant modifiers when rule specifies the related alteration concept
    Given the classification config has the following gene_variant_modifiers:
      | value                    |
      | FLT3_ITD                 |
      | CEBPA_BIALLELIC_MUTATION |
      | MET_EXON_14_SKIPPING     |

    And the value of has_nonexonic_variants is true
    And a RuleSet with the following therapy rules -new:
      | drug      | disease_type           | response_to_drugs   | in                       | out | refractory |
      | Sorafenib | Acute Myeloid Leukemia | Primary sensitivity | FLT3 ITD                 |     | NCCN       |
      | Afatinib  | Acute Myeloid Leukemia | Primary sensitivity | MET Exon 14 Skipping     |     | NCCN       |
      | Erlotinib | Acute Myeloid Leukemia | Primary sensitivity | CEBPA Biallelic Mutation |     | NCCN       |

    And an "Acute Myeloid Leukemia" Analysis with the following results:
      | gene  | g_change    | aa_change | decision_result | is_reported | mutation_type        | classification | gene_variant_modifier_values |
      | FLT3  | c.1705-1G>T |           | MUT             | false       | Splice Acceptor Site | Uncertain      | FLT3_ITD                     |
      | MET   | c.3082+1G>T |           | MUT             | false       | Splice Donor Site    | Uncertain      | MET_EXON_14_SKIPPING         |
      | CEBPA | c.*197G>A   |           | MUT             | false       | Non-Coding           | Uncertain      | CEBPA_BIALLELIC_MUTATION     |

    When I generate therapy summary
    Then I should get the following results:
      | drug      | variant_summary          | response_to_drugs   | setting_name | setting_value | on_label | disease_name           |
      | Afatinib  | MET Exon 14 Skipping     | Primary sensitivity | Refractory   | NCCN          | true     | Acute Myeloid Leukemia |
      | Erlotinib | CEBPA Biallelic Mutation | Primary sensitivity | Refractory   | NCCN          | true     | Acute Myeloid Leukemia |
      | Sorafenib | FLT3 ITD                 | Primary sensitivity | Refractory   | NCCN          | true     | Acute Myeloid Leukemia |


  Scenario: No therapy for variants with gene variant modifiers when the variant is not detected, or for variants without gene variant modifiers
    Given the classification config has the following gene_variant_modifiers:
      | value                    |
      | FLT3_ITD                 |
      | CEBPA_BIALLELIC_MUTATION |
      | MET_EXON_14_SKIPPING     |

    And the value of has_nonexonic_variants is true
    And a RuleSet with the following therapy rules:
      | drug      | disease_type           | response_to_drugs   | in                       | out | refractory |
      | Sorafenib | Acute Myeloid Leukemia | Primary sensitivity | FLT3 ITD                 |     | NCCN, MCG  |
      | Sorafenib | Acute Myeloid Leukemia | Primary sensitivity | Met Exon 14 Skipping     |     | NCCN, MCG  |
      | Sorafenib | Acute Myeloid Leukemia | Primary sensitivity | CEBPA Biallelic Mutation |     | NCCN, MCG  |

    And an "Acute Myeloid Leukemia" Analysis with the following results:
      | gene  | g_change                                              | aa_change    | decision_result | is_reported | mutation_type          | gene_variant_modifier_values |
      | FLT3  | c.1777_1815dupGATTTCAGAGAATATGAATATGATCTCAAATGGGAGTTT | D593_F605dup | MUT             | false       | Insertion - In Frame   |                              |
      | FLT3  | c.1829_1830insGCCT                                    | E611Pfs*     | ND              | false       | Insertion - Frameshift | FLT3_ITD                     |
      | MET   | c.3029C>T                                             | T1010I       | MUT             | false       | Insertion - In Frame   |                              |
      | CEBPA | c.940G>A                                              | V314M        | ND              | false       | Insertion - In Frame   | CEBPA_BIALLELIC_MUTATION     |

    When I generate therapy summary
    Then I should get no therapy results

  Scenario: Generate therapy when gene variant modifier concept not detected and the concept is specified as out variant (reflex not enabled)
    Given the test regions for the SNV test mode include the following genes: FLT3,CEBPA,MET
    Given the classification config has the following gene_variant_modifiers:
      | value                    |
      | FLT3_ITD                 |
      | CEBPA_BIALLELIC_MUTATION |
      | MET_EXON_14_SKIPPING     |
    And the value of has_nonexonic_variants is true
    And the product does not have reflex enabled
    And a RuleSet with the following therapy rules:
      | drug      | disease_type           | response_to_drugs   | in | out                                                      | refractory |
      | Sorafenib | Acute Myeloid Leukemia | Primary sensitivity |    | FLT3 ITD, CEBPA Biallelic Mutation, MET Exon 14 Skipping | NCCN, MCG  |

    And an "Acute Myeloid Leukemia" Analysis for an "SNV+CTX" Order with the following results:
      | gene  | g_change                                              | aa_change    | decision_result | is_reported | mutation_type        | gene_variant_modifier_values |
      | FLT3  | c.1777_1815dupGATTTCAGAGAATATGAATATGATCTCAAATGGGAGTTT | D593_F605dup | ND              | false       | Insertion - In Frame |                              |
      | MET   | c.3029C>T                                             | T1010I       | ND              | false       | Insertion - In Frame | MET_EXON_14_SKIPPING         |
      | CEBPA | c.940G>A                                              | V314M        | MUT             | false       | Insertion - In Frame |                              |

    When I generate therapy summary
    Then I should get the following results:
      | drug      | variant_summary                                                                             | response_to_drugs   | setting_name | setting_value | on_label | disease_name           |
      | Sorafenib | Relevant alterations not detected: FLT3 ITD, CEBPA Biallelic Mutation, MET Exon 14 Skipping | Primary sensitivity | Refractory   | NCCN, MCG     | true     | Acute Myeloid Leukemia |


  Scenario Outline: Generate therapy when FLT3 ITD not detected and FLT3 ITD specified as out variant if FLT3 not completely hidden by reflex
    Given the classification config has the following gene_variant_modifiers:
      | value    |
      | FLT3_ITD |
    And the value of has_nonexonic_variants is true
    And the product has reflex enabled

    And the product uses test regions with the following genes:
      | name   | reflex_group |
      | FLT3   | 1            |
      | DNMT3A | 2            |

    And the FLT3 test region has the following segments:
      | chr | s        | e        | reflex_group_override |
      | 13  | 28592599 | 28592771 |                       |
      | 13  | 28607914 | 28608514 | 3                     |

    And it has an SNV Workbench Config with the following tabs and Criteria:
      | tab_name            | criteria                       | reflex_groups |
      | FLT3 Segment1       | reflexgroup:1                  | 1             |
      | Second Reflex Group | reflexgroup:2                  | 2             |
      | FLT3 Segment2       | reflexgroup:3 OR reflexgroup:0 | 3             |

    And a RuleSet with the following therapy rules:
      | drug      | disease_type           | response_to_drugs   | in | out      | refractory |
      | Sorafenib | Acute Myeloid Leukemia | Primary sensitivity |    | FLT3 ITD | NCCN, MCG  |

    And an "Acute Myeloid Leukemia" Analysis for an "SNV+CTX" Order with the following results:
      | gene | g_change                                              | aa_change    | decision_result | is_reported | mutation_type        | gene_variant_modifier_values | tab           |
      | FLT3 | c.1777_1815dupGATTTCAGAGAATATGAATATGATCTCAAATGGGAGTTT | D593_F605dup | ND              | false       | Insertion - In Frame |                              | FLT3 Segment2 |

    And the analysis has the following reflex status:
      | reflex_tabs_open |
      | <reflex>         |

    When I generate therapy summary
    Then I should get the following results:
      | drug      | variant_summary                             | response_to_drugs   | setting_name | setting_value | on_label | disease_name           |
      | Sorafenib | Relevant alterations not detected: FLT3 ITD | Primary sensitivity | Refractory   | NCCN, MCG     | true     | Acute Myeloid Leukemia |

    Examples:
      | reflex                             |
      | FLT3 Segment1                      |
      | FLT3 Segment1::Second Reflex Group |
      | Second Reflex Group::FLT3 Segment2 |
      | FLT3 Segment2                      |

  Scenario: Do Not Generate therapy when FLT3 ITD not detected and FLT3 ITD specified as out variant if FLT3 completely hidden by reflex
    Given the classification config has the following gene_variant_modifiers:
      | value    |
      | FLT3_ITD |
    And the value of has_nonexonic_variants is true

    And the product has reflex enabled

    And the product uses test regions with the following genes:
      | name   | reflex_group |
      | FLT3   | 1            |
      | DNMT3A | 2            |
    And the FLT3 test region has the following segments:
      | chr | s        | e        | reflex_group_override |
      | 13  | 28592599 | 28592771 |                       |
      | 13  | 28607914 | 28608514 | 3                     |
    And it has an SNV Workbench Config with the following tabs and Criteria:
      | tab_name      | criteria                       | reflex_groups |
      | FLT3 Segment1 | reflexgroup:1                  | 1             |
      | DNMT3A        | reflexgroup:2                  | 2             |
      | FLT3 Segment2 | reflexgroup:3 OR reflexgroup:0 | 3             |

    And a RuleSet with the following therapy rules:
      | drug      | disease_type           | response_to_drugs   | in | out      | refractory |
      | Sorafenib | Acute Myeloid Leukemia | Primary sensitivity |    | FLT3 ITD | NCCN, MCG  |

    And an "Acute Myeloid Leukemia" Analysis for an "SNV+CTX" Order with the following results:
      | gene | g_change                                              | aa_change    | decision_result | is_reported | mutation_type        | gene_variant_modifier_values | tab           |
      | FLT3 | c.1777_1815dupGATTTCAGAGAATATGAATATGATCTCAAATGGGAGTTT | D593_F605dup | ND              | false       | Insertion - In Frame |                              | FLT3 Segment2 |

    And the analysis has the following reflex status:
      | reflex_tabs_open |
      | DNMT3A           |

    When I generate prognosis summary
    Then I should get no therapy results

  Scenario: Do not generate therapy when variant with modifier is detected and the related concept is specified as out variant
    Given the test regions for the SNV test mode include the following genes: FLT3,MET,CEBPA
    And the classification config has the following gene_variant_modifiers:
      | value                    |
      | FLT3_ITD                 |
      | CEBPA_BIALLELIC_MUTATION |
      | MET_EXON_14_SKIPPING     |
    And the value of has_nonexonic_variants is true

    And a RuleSet with the following therapy rules:
      | drug      | disease_type           | response_to_drugs   | in | out                      | refractory |
      | Sorafenib | Acute Myeloid Leukemia | Primary sensitivity |    | FLT3 ITD                 | NCCN, MCG  |
      | Sorafenib | Acute Myeloid Leukemia | Primary sensitivity |    | CEBPA Biallelic Mutation | NCCN, MCG  |
      | Sorafenib | Acute Myeloid Leukemia | Primary sensitivity |    | MET Exon 14 Skipping     | NCCN, MCG  |

    And an "Acute Myeloid Leukemia" Analysis for an "SNV+CTX" Order with the following results:
      | gene  | g_change                                              | aa_change    | decision_result | is_reported | mutation_type        | gene_variant_modifier_values |
      | FLT3  | c.1777_1815dupGATTTCAGAGAATATGAATATGATCTCAAATGGGAGTTT | D593_F605dup | MUT             | false       | Insertion - In Frame | FLT3_ITD                     |
      | MET   | c.3029C>T                                             | T1010I       | MUT             | false       | Insertion - In Frame | MET_EXON_14_SKIPPING         |
      | CEBPA | c.940G>A                                              | V314M        | MUT             | false       | Insertion - In Frame | CEBPA_BIALLELIC_MUTATION     |

    When I generate therapy summary
    Then I should get no therapy results

#######################################################################################################
#######################################################################################################
#######################################################################################################





