def get_temple_recommendation(name, age, location, preference):
    # Rule-based temple logic
    safe_temples = {
        "historical": ["Konark Sun Temple", "Khajuraho Temple", "Brihadeeswarar Temple"],
        "peaceful": ["Golden Temple", "Ramanathaswamy Temple", "ISKCON Bangalore"],
        "south indian": ["Tirupati Balaji", "Meenakshi Temple", "Murudeshwar Temple"]
    }

    suggestion = safe_temples.get(preference.lower(), ["Generic Temple 1", "Generic Temple 2"])

    response = f"""
    Hello {name}, here’s your safe and senior-friendly temple tour plan:

    ✅ Recommended Temples based on your preference:
    - {suggestion[0]}
    - {suggestion[1]}
    - {suggestion[2]}

    🧳 Travel Tips:
    - Start early in the morning
    - Prefer AC cabs with low floor entry
    - Carry medicines, ID, and a contact card

    ⏰ Darshan Timings:
    - Morning: 6:00 AM – 11:00 AM
    - Evening: 5:00 PM – 9:00 PM

    🙏 Stay blessed and safe!
    """
    return response
