# import libraries
from fastapi import FastAPI, Path, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, computed_field
from typing import Annotated, Literal, Optional
import json

# Initialize FastAPI app
app = FastAPI()

# Define the Patient model
class Patient(BaseModel):
    id : Annotated[str, Field(..., description="Id of the patient", examples=["P001"])]
    name : Annotated[str, Field(..., description="Name of the patient")] 
    city : Annotated[str, Field(..., description="Name of the city where the patient is living ")] 
    age : Annotated[int, Field(..., gt=0, le=120, description="The age of the patient")]
    gender : Annotated[Literal["Male","Female","Other"], Field(..., description="Gender of the patient")]
    height : Annotated[float, Field(..., gt=0, description="Height of the patient in meters")]
    weight : Annotated[float, Field(..., gt=0, description="Weight of the patient in kgs")]

    # Computed fields for BMI 
    @computed_field
    @property
    def bmi(self)-> float:
        calculated_bmi = round(self.weight/(self.height**2),2)
        return calculated_bmi
    
    # Computed fields for Verdict
    @computed_field
    @property
    def verdict(self)-> str:
        if self.bmi < 18.5:
            return "Underweight"
        elif self.bmi < 25:
            return "Normal weight"
        elif self.bmi < 30:
            return "Overweight"
        else:
            return "Obese"

# Define the UpdatePatient model for partial updates
class UpdatePatient(BaseModel):
    name : Annotated[Optional[ str], Field(default=None, description="Name of the patient")] 
    city : Annotated[Optional[ str], Field(default=None, description="Name of the city where the patient is living ")] 
    age : Annotated[Optional[int], Field(default=None, gt=0, le=120, description="The age of the patient")]
    gender : Annotated[Optional[Literal["Male","Female","Other"]], Field(default=None, description="Gender of the patient")]
    height : Annotated[Optional[float], Field(default=None, gt=0, description="Height of the patient in meters")]
    weight : Annotated[Optional[float], Field(default=None, gt=0, description="Weight of the patient in kgs")]

# function for getting data
def get_data():
    with open("patients.json", "r") as f :
        return json.load(f)
    
# function for saving data
def save_data(data):
    with open("patients.json", "w") as f :
        json.dump(data, f)

# Define the API endpoints
@app.get("/")
def hello():
    return {"massage": "Patient Management System API"}

# Define the about endpoint
@app.get("/about")
def about():
    return {"massage": "A fully functional API for managing patient records."}

# Define the view endpoint to get all patients
@app.get("/view")
def view():
    #Load the patient
    data = get_data()
    return data

# Define the view endpoint to get a specific patient by ID
@app.get("/patient/{patient_id}")
def view_patient(patient_id: str = Path(..., description="Give the ID of patient", example="P001")):
    #Load the patient
    data = get_data()
    if patient_id in data:
        return data[patient_id]
    else:
        raise HTTPException(status_code=404, detail="Patient not found")

# Define the sort endpoint to sort patients by height, weight, or BMI
@app.get("/sort")
def sort_patient(sort_by: str = Query(...,  description="Sort in the basis of Height , Weight or BMI", example="height"), order: str = Query("asc", description="Sort in asc or desc order")):
    valid_fields = ["height","weight","bmi"]

    if sort_by not in valid_fields:
        raise HTTPException(status_code=404, detail="The input is not valid")
    if order not in ["asc","desc"]:
        raise HTTPException(status_code=404, detail="The input is not valid")
    
    
    data = get_data()

    sort_order= True if order =="desc" else False
    sorted_patient = sorted(data.values(),key=lambda x : x.get(sort_by,0), reverse=sort_order)

    return sorted_patient


# # Create new Patient
@app.post("/create")
def create_patient(patient : Patient) :
    # load existing data
    data = get_data()

    # check if the patient already exists
    if patient.id in data:
        raise HTTPException(status_code=401, detail="The patient is already exists")
    
    # new patient insert into the database
    data[patient.id]=patient.model_dump(exclude="id")

    # save into the json file
    save_data(data)

    return JSONResponse(status_code=201, content={"massage":"Patient created successfully"})
    

# Update existing Patient
@app.put("/edit/{patient_id}")
def update_patient(patient_id: Annotated[str, Path(description="ID of the patient to update", example="P001")], patient_update: UpdatePatient):
    # load existing data
    data = get_data()

    # check if the patient exists
    if patient_id not in data:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    # update the patient data
    patient_data = data[patient_id]
    updated_data = patient_update.model_dump(exclude_unset=True)

    for key in updated_data:
        patient_data[key] = updated_data[key]

    # convert the updated data back to Patient model
    patient_data['id'] = patient_id  # Ensure the ID is set
    patient_data.pop('bmi', None)  # Remove bmi as it is a computed field
    patient_data.pop('verdict', None)  # Remove verdict as it is a computed field
    patient_obj = Patient(**patient_data)

    patient_data = patient_obj.model_dump(exclude="id")  # Exclude the ID for storage

    # save into the json file
    data[patient_id] = patient_data
    save_data(data)

    return JSONResponse(status_code=200, content={"massage":"Patient updated successfully"})


# Delete existing Patient
@app.delete("/delete/{patient_id}")
def delete_patient(patient_id: Annotated[str, Path(description="ID of the patient to delete", example="P001")]):
    # load existing data
    data = get_data()

    # check if the patient exists
    if patient_id not in data:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    # detete the patient data
    del data[patient_id]

    # save into the json file
    save_data(data)

    return JSONResponse(status_code=200, content={"massage":"Patient deleted successfully"})
