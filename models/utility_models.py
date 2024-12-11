from dataclasses import dataclass
from typing import List

@dataclass
class BaseResponseType:
    message: str

@dataclass
class ListResponseType(BaseResponseType):
    data_list: List[object] 

@dataclass
class ObjectResponseType(BaseResponseType):
    data_object: object 
