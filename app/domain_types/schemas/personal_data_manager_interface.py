from abc import ABC, abstractmethod
from app.domain_types.schemas.llm_service import PersonalDataCollection

class IPersonalDataManager(ABC):

    @abstractmethod
    def store_personal_data(self, client_name, data_object:PersonalDataCollection):
        pass

    @abstractmethod
    def retrieve_personal_data(self, user_id):
        pass









# from datetime import date
# from typing import Optional
# from pydantic import BaseModel


# class BloodGroup(str):
#     pass

# class Severity(str):
#     pass

# class HealthProfileDomainModel(BaseModel):
#     id: Optional[str]
#     PatientUserId: Optional[str]
#     BloodGroup: Optional[BloodGroup]
#     BloodTransfusionDate: Optional[date]
#     BloodDonationCycle: Optional[int]
#     MajorAilment: Optional[str]
#     OtherConditions: Optional[str]
#     IsDiabetic: Optional[bool]
#     HasHeartAilment: Optional[bool]
#     MaritalStatus: Optional[str]
#     Ethnicity: Optional[str]
#     Race: Optional[str]
#     Nationality: Optional[str]
#     Occupation: Optional[str]
#     SedentaryLifestyle: Optional[bool]
#     IsSmoker: Optional[bool]
#     SmokingSeverity: Optional[Severity]
#     SmokingSince: Optional[date]
#     IsDrinker: Optional[bool]
#     DrinkingSeverity: Optional[Severity]
#     DrinkingSince: Optional[date]
#     SubstanceAbuse: Optional[bool]
#     ProcedureHistory: Optional[str]
#     ObstetricHistory: Optional[str]
#     OtherInformation: Optional[str]
#     TobaccoQuestion: Optional[str]
#     TobaccoQuestionAns: Optional[bool]
#     TypeOfStroke: Optional[str]
#     HasHighBloodPressure: Optional[bool]
#     HasHighCholesterol: Optional[bool]
#     HasAtrialFibrillation: Optional[bool]
#     StrokeSurvivorOrCaregiver: Optional[str]
#     LivingAlone: Optional[bool]
#     WorkedPriorToStroke: Optional[bool]

#     class Config:
#         arbitrary_types_allowed = True
