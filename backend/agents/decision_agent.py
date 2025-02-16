from typing import Dict, Any, Optional

# ---------------------------------------------------------
# 4. Decision (Cross-Checking) Agent (Stub)
# ---------------------------------------------------------
class DecisionAgent:
    """
    Agent responsible for combining all extracted data and making a final verification decision.
    Could be powered by an LLM (like Llama, GPT, or other) or a rule-based engine.
    """
    def __init__(self):
        pass

    def make_final_decision(
        self, 
        parsed_data: Dict[str, Any], 
        face_similarity: float, 
        osint_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Aggregates all sub-agent results and generates a final decision.

        Args:
            parsed_data (Dict[str, Any]): The structured data from the ID.
            face_similarity (float): The face similarity score from FaceVerificationAgent.
            osint_data (Dict[str, Any]): The OSINT findings.

        Returns:
            Dict[str, Any]: Final decision output, including a confidence score and reasoning.
                {
                    "verificationScore": 0.95,
                    "status": "LIKELY_VALID",
                    "reasoning": "Face match is 85%. OSINT data consistent."
                }
        """
        # Example logic:
        #  - If face_similarity < 0.7 => High suspicion
        #  - If OSINT confidence < 0.5 => Uncertain
        #  - Additional checks on dateOfBirth vs. OSINT age
        #  - If no contradictions => likely valid

        reasoning_notes = []
        confidence = 0.0

        # Basic rule-based approach (simplified)
        if face_similarity < 0.7:
            reasoning_notes.append(f"Low face similarity: {face_similarity:.2f}")
            final_status = "REJECT"
            confidence = 0.3
        else:
            reasoning_notes.append(f"Acceptable face similarity: {face_similarity:.2f}")
            confidence += face_similarity * 0.4  # Weighted 40%

        osint_confidence = osint_data.get("consolidatedConfidence", 0.0)
        if osint_confidence < 0.5:
            reasoning_notes.append(f"Low OSINT confidence: {osint_confidence:.2f}")
            confidence += 0.1
            final_status = "REVIEW"
        else:
            reasoning_notes.append(f"OSINT data is consistent: {osint_confidence:.2f}")
            confidence += osint_confidence * 0.4

        # Check if DOB matches OSINT-based age (rough example)
        id_dob = parsed_data.get("dateOfBirth", "")
        # If you want to parse the date and cross-check age, do so here

        # Summarize final confidence
        if confidence > 0.75:
            final_status = "LIKELY_VALID"
        elif confidence < 0.5:
            final_status = "LIKELY_FRAUD"
        else:
            final_status = "REVIEW"

        reasoning = " | ".join(reasoning_notes)
        return {
            "verificationScore": round(confidence, 2),
            "status": final_status,
            "reasoning": reasoning
        }