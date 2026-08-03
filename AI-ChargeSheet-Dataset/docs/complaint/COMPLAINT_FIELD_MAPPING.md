# Complaint Field Mapping

- Complaint title -> derived from case information
- Complainant name -> MasterCase.victim.full_name
- Incident date -> MasterCase.case_information.incident_date
- Place of occurrence -> MasterCase.case_information.location
- Offence description -> MasterCase.case_information.offence_description
- Accused names -> MasterCase.accused[].full_name
