# FIR Field Mapping to MasterCase

This document maps every FIR field in the redesigned schema to the validated MasterCase model.

## Header and registration

- FIR number -> MasterCase.case_information.FIR_number
- FIR date -> MasterCase.case_information.FIR_date
- Police station -> MasterCase.case_information.police_station
- District -> MasterCase.case_information.district
- State -> MasterCase.case_information.state
- Crime category -> MasterCase.case_information.crime_category
- Offence description -> MasterCase.case_information.offence_description

## Occurrence details

- Incident date -> MasterCase.case_information.incident_date
- Incident time -> MasterCase.case_information.incident_time
- Place of occurrence -> MasterCase.case_information.location

## Complainant details

- Complainant name -> MasterCase.victim.full_name
- Complainant age -> MasterCase.victim.age
- Complainant gender -> MasterCase.victim.gender
- Complainant occupation -> MasterCase.victim.occupation
- Complainant address -> MasterCase.victim.address
- Complainant phone -> MasterCase.victim.phone

## Accused details

- Known accused names -> MasterCase.accused[].full_name
- Accused aliases -> MasterCase.accused[].alias_names
- Accused charges -> MasterCase.accused[].charges
- Accused custody status -> MasterCase.accused[].custody_status

## Witness details

- Witness names -> MasterCase.witnesses[].full_name
- Witness relationship -> MasterCase.witnesses[].relationship_to_case
- Witness statement summary -> MasterCase.witnesses[].statement_summary

## Evidence and property details

- Evidence items -> MasterCase.evidence[]
- Evidence description -> MasterCase.evidence[].description
- Recovered from -> MasterCase.evidence[].recovered_from
- Seizure date -> MasterCase.evidence[].seizure_date
- Forensic requirement -> MasterCase.evidence[].forensic_required

## Investigation details

- Investigating officer name -> MasterCase.investigating_officer.name
- Investigating officer rank -> MasterCase.investigating_officer.rank
- Investigating officer buckle number -> MasterCase.investigating_officer.buckle_number
- Investigating officer police station -> MasterCase.investigating_officer.police_station

## Legal and narrative sections

- Applicable legal sections -> MasterCase.applicable_bns_sections.sections[]
- Narrative body -> MasterCase.case_information.offence_description
- Complaint summary -> Derived from MasterCase victim and case information
- Registration notes -> Derived from MasterCase case information and investigating officer details
# FIR Field Mapping to MasterCase

This document maps every FIR field to the validated MasterCase source of truth.

## Header and registration

- FIR Number -> MasterCase.case_information.FIR_number
- FIR Date -> MasterCase.case_information.FIR_date
- Police Station -> MasterCase.case_information.police_station
- District -> MasterCase.case_information.district
- State -> MasterCase.case_information.state
- Crime Category -> MasterCase.case_information.crime_category
- Offence Description -> MasterCase.case_information.offence_description

## Occurrence details

- Incident Date -> MasterCase.case_information.incident_date
- Incident Time -> MasterCase.case_information.incident_time
- Place of Occurrence -> MasterCase.case_information.location

## Complainant

- Complainant Name -> MasterCase.victim.full_name
- Complainant Age -> MasterCase.victim.age
- Complainant Gender -> MasterCase.victim.gender
- Complainant Occupation -> MasterCase.victim.occupation
- Complainant Address -> MasterCase.victim.address
- Complainant Phone -> MasterCase.victim.phone

## Accused

- Known Accused Name -> MasterCase.accused[].full_name
- Accused Age -> MasterCase.accused[].age
- Accused Gender -> MasterCase.accused[].gender
- Accused Occupation -> MasterCase.accused[].occupation
- Accused Address -> MasterCase.accused[].address
- Accused Alias Names -> MasterCase.accused[].alias_names
- Accused Charges -> MasterCase.accused[].charges

## Witnesses

- Witness Name -> MasterCase.witnesses[].full_name
- Witness Relationship -> MasterCase.witnesses[].relationship_to_case
- Witness Statement Summary -> MasterCase.witnesses[].statement_summary

## Evidence and property

- Evidence Description -> MasterCase.evidence[].description
- Evidence Type -> MasterCase.evidence[].evidence_type
- Recovered From -> MasterCase.evidence[].recovered_from
- Seizure Date -> MasterCase.evidence[].seizure_date

## Investigation and officer details

- Investigating Officer Name -> MasterCase.investigating_officer.name
- Investigating Officer Rank -> MasterCase.investigating_officer.rank
- Investigating Officer Buckle Number -> MasterCase.investigating_officer.buckle_number
- Investigating Officer Police Station -> MasterCase.investigating_officer.police_station

## Narrative

- Complaint Narrative -> MasterCase.case_information.offence_description
- Additional Narrative Notes -> MasterCase.victim.statement_summary or MasterCase.witnesses[].statement_summary

## Legal sections

- Applicable Sections -> MasterCase.applicable_bns_sections.sections[]
