export interface Interaction {
  with: string;
  risk: 'LOW' | 'MEDIUM' | 'HIGH';
  description: string;
}

export interface Medicine {
  name: string;
  salt: string;
  interactions: Interaction[];
}

export const medicineDb: Medicine[] = [
  {
    "name": "Aspirin",
    "salt": "Acetylsalicylic acid",
    "interactions": [
      {
        "with": "Warfarin",
        "risk": "HIGH",
        "description": "Increased risk of bleeding due to combined anticoagulant effects."
      },
      {
        "with": "Ibuprofen",
        "risk": "MEDIUM",
        "description": "May decrease the antiplatelet effect of aspirin and increase gastric irritation."
      },
      {
        "with": "Clopidogrel",
        "risk": "HIGH",
        "description": "Significantly increased risk of major bleeding."
      }
    ]
  },
  {
    "name": "Warfarin",
    "salt": "Warfarin Sodium",
    "interactions": [
      {
        "with": "Aspirin",
        "risk": "HIGH",
        "description": "Increased risk of bleeding."
      },
      {
        "with": "Vitamin K",
        "risk": "MEDIUM",
        "description": "Vitamin K can decrease the effectiveness of Warfarin."
      },
      {
        "with": "Alcohol",
        "risk": "MEDIUM",
        "description": "Can affect how the body metabolizes Warfarin."
      }
    ]
  },
  {
    "name": "Ibuprofen",
    "salt": "Ibuprofen",
    "interactions": [
      {
        "with": "Aspirin",
        "risk": "MEDIUM",
        "description": "May decrease the antiplatelet effect of aspirin."
      },
      {
        "with": "Lisinopril",
        "risk": "MEDIUM",
        "description": "May reduce the blood pressure lowering effect of Lisinopril."
      }
    ]
  },
  {
    "name": "Paracetamol",
    "salt": "Acetaminophen",
    "interactions": [
      {
        "with": "Alcohol",
        "risk": "MEDIUM",
        "description": "Increased risk of liver damage with chronic or heavy alcohol use."
      }
    ]
  },
  {
    "name": "Lisinopril",
    "salt": "Lisinopril",
    "interactions": [
      {
        "with": "Ibuprofen",
        "risk": "MEDIUM",
        "description": "May reduce the blood pressure lowering effect."
      },
      {
        "with": "Potassium Supplements",
        "risk": "HIGH",
        "description": "Increased risk of high potassium levels in the blood (hyperkalemia)."
      }
    ]
  },
  {
    "name": "Metformin",
    "salt": "Metformin Hydrochloride",
    "interactions": [
      {
        "with": "Contrast Dye",
        "risk": "HIGH",
        "description": "Risk of lactic acidosis; usually stopped before imaging procedures."
      }
    ]
  },
  {
    "name": "Atorvastatin",
    "salt": "Atorvastatin Calcium",
    "interactions": [
      {
        "with": "Grapefruit Juice",
        "risk": "MEDIUM",
        "description": "Can increase the levels of statin in your blood, increasing side effect risk."
      }
    ]
  }
];
