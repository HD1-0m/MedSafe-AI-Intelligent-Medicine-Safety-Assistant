import { Medicine, medicineDb } from './medicineDb';

export function identifyMedicine(query: string): Medicine | null {
  const normalizedQuery = query.toLowerCase().trim();
  if (!normalizedQuery) return null;

  // Simple exact or partial match for now
  // In a real app, we'd use a fuzzy matching library like Fuse.js or RapidFuzz
  return medicineDb.find(m => 
    m.name.toLowerCase() === normalizedQuery || 
    m.salt.toLowerCase() === normalizedQuery ||
    m.name.toLowerCase().includes(normalizedQuery)
  ) || null;
}

export function checkInteractions(selectedMeds: Medicine[]) {
  const interactions: { pair: [string, string], risk: string, description: string }[] = [];
  const names = selectedMeds.map(m => m.name.toLowerCase());

  selectedMeds.forEach(med => {
    med.interactions.forEach(interaction => {
      if (names.includes(interaction.with.toLowerCase())) {
        const pair: [string, string] = [med.name, interaction.with];
        const sortedPair = [...pair].sort();
        
        // Avoid duplicates
        const exists = interactions.some(i => 
          i.pair[0] === sortedPair[0] && i.pair[1] === sortedPair[1]
        );

        if (!exists) {
          interactions.push({
            pair: sortedPair as [string, string],
            risk: interaction.risk,
            description: interaction.description
          });
        }
      }
    });
  });

  return interactions;
}

export function calculateOverallRisk(symptoms: string[], interactions: any[]) {
  let score = 0;
  const reasons: string[] = [];

  // Interaction risks
  interactions.forEach(i => {
    if (i.risk === 'HIGH') score = Math.max(score, 3);
    else if (i.risk === 'MEDIUM') score = Math.max(score, 2);
    else score = Math.max(score, 1);
    reasons.push(`Interaction: ${i.pair[0]} + ${i.pair[1]} (${i.risk})`);
  });

  // Basic symptom risk (simplified)
  const highRiskSymptoms = ['chest pain', 'breathing', 'allergic', 'unconscious'];
  symptoms.forEach(s => {
    const sl = s.toLowerCase();
    if (highRiskSymptoms.some(h => sl.includes(h))) {
      score = Math.max(score, 3);
      reasons.push(`High-risk symptom: ${s}`);
    } else {
      score = Math.max(score, 1);
      reasons.push(`Symptom: ${s}`);
    }
  });

  const severity = score === 3 ? 'HIGH' : (score === 2 ? 'MEDIUM' : 'LOW');
  return { severity, reasons, score };
}
