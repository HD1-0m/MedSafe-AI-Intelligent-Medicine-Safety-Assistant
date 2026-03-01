import { GoogleGenAI } from "@google/genai";

const ai = new GoogleGenAI({ apiKey: process.env.GEMINI_API_KEY || "" });

export async function explainRisk(severity: string, reasons: string[]) {
  const model = "gemini-3-flash-preview";
  const prompt = `As a medical safety assistant, provide a friendly, empathetic medical guidance paragraph for the following situation.
  Severity: ${severity}. 
  Reasons: ${reasons.join(", ")}. 
  
  Structure the response exactly like this:
  "Hey there! We're here to help you tackle that [problem]... [Friendly advice with emojis like 🧘, 👁️, 🧘]...
  
  In addition to these tips, here are a couple of extra home remedies you can try...
  
  Warning sign to watch: [Serious symptoms that require medical attention]"
  
  Use a warm, supportive tone. Do not provide a diagnosis.`;

  try {
    const response = await ai.models.generateContent({
      model,
      contents: prompt,
    });
    return response.text || "No advice available at the moment.";
  } catch (error) {
    console.error("Gemini Error:", error);
    return "I'm sorry, I encountered an error while generating your advice. Please consult a professional.";
  }
}

export async function monitorSideEffects(age: string, gender: string, meds: string, doses: string) {
  const model = "gemini-3-flash-preview";
  const prompt = `Analyze potential side effects for a ${age} year old ${gender} taking these medicines: ${meds} at these doses: ${doses}.
  Provide a friendly advice paragraph including:
  1. Common side effects to watch for.
  2. Tips to manage them.
  3. When to be concerned.
  Use the "Hey there!" friendly paragraph style.`;

  try {
    const response = await ai.models.generateContent({
      model,
      contents: prompt,
    });
    return response.text || "No side effect data available.";
  } catch (error) {
    return "Error monitoring side effects.";
  }
}

export async function predictEmergencyRisk(symptoms: string, history: string) {
  const model = "gemini-3-flash-preview";
  const prompt = `Predict emergency risk for these symptoms: "${symptoms}". Patient history: "${history}".
  Classify as LOW, MEDIUM, or HIGH.
  Provide a friendly advice paragraph explaining the risk and immediate steps.
  Use the "Hey there!" friendly paragraph style.`;

  try {
    const response = await ai.models.generateContent({
      model,
      contents: prompt,
    });
    return response.text || "No risk prediction available.";
  } catch (error) {
    return "Error predicting emergency risk.";
  }
}

export async function parsePrescription(base64Image: string, mimeType: string) {
  const model = "gemini-3-flash-preview";
  const prompt = "Extract medicine names and dosages from this prescription image. Return it as a structured markdown list. If you see any handwriting, try your best to decipher it.";

  try {
    const response = await ai.models.generateContent({
      model,
      contents: {
        parts: [
          { text: prompt },
          {
            inlineData: {
              data: base64Image.split(",")[1] || base64Image,
              mimeType: mimeType,
            },
          },
        ],
      },
    });
    return response.text || "No text could be extracted.";
  } catch (error) {
    console.error("Gemini OCR Error:", error);
    return "Failed to parse prescription. Ensure the image is clear and try again.";
  }
}

export async function evaluateSymptoms(symptoms: string) {
  const model = "gemini-3-flash-preview";
  const prompt = `Analyze these symptoms: "${symptoms}". 
  Provide a preliminary risk assessment (LOW, MEDIUM, HIGH) and educational context. 
  Identify potential emergency signs. 
  IMPORTANT: State clearly that this is not a diagnosis. 
  Format the response as JSON with keys: "severity" (string), "reasons" (array of strings), "guidance" (string).`;

  try {
    const response = await ai.models.generateContent({
      model,
      contents: prompt,
      config: {
        responseMimeType: "application/json"
      }
    });
    return JSON.parse(response.text || "{}");
  } catch (error) {
    console.error("Gemini Symptom Error:", error);
    return { severity: "UNKNOWN", reasons: ["Error analyzing symptoms"], guidance: "Please consult a professional." };
  }
}
