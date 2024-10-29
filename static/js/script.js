// Update the parseTimestamp method to better handle time-only formats
parseTimestamp(timeStr) {
    try {
        if (!timeStr) return null;

        // Handle time-only format (HH:MM AM/PM)
        const timeOnlyRegex = /^(\d{1,2}):(\d{2})\s*(AM|PM)$/i;
        const timeOnlyMatch = timeStr.match(timeOnlyRegex);
        if (timeOnlyMatch) {
            const [_, hours, minutes, period] = timeOnlyMatch;
            const date = new Date();
            let hour = parseInt(hours, 10);
            
            if (period.toLowerCase() === 'pm' && hour < 12) {
                hour += 12;
            } else if (period.toLowerCase() === 'am' && hour === 12) {
                hour = 0;
            }
            
            date.setHours(hour, parseInt(minutes, 10), 0);
            return date;
        }

        // Handle date with time format
        const dateTimeRegex = /^([A-Za-z]+\s+\d{1,2}),\s*(\d{1,2}):(\d{2})\s*(AM|PM)$/i;
        const match = timeStr.match(dateTimeRegex);
        if (match) {
            const [_, dateStr, hours, minutes, period] = match;
            const currentYear = new Date().getFullYear();
            const fullDateStr = `${dateStr}, ${currentYear} ${hours}:${minutes} ${period}`;
            const parsedDate = new Date(fullDateStr);
            if (!isNaN(parsedDate.getTime())) {
                return parsedDate;
            }
        }

        // Try parsing as ISO date
        const parsedDate = new Date(timeStr);
        if (!isNaN(parsedDate.getTime())) {
            return parsedDate;
        }

        console.warn('Could not parse timestamp:', timeStr);
        return new Date();

    } catch (error) {
        console.error('Error parsing timestamp:', error);
        return new Date();
    }
}
