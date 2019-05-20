class Show:
    def __init__(self, raw, dates, bands, venue, city, age, age_notes, price,
                 price_notes, time, time_notes, features, notes):
        self.raw = raw
        self.dates = dates
        self.bands = bands
        self.venue = venue
        self.city = city
        self.age = age
        self.age_notes = age_notes
        self.price = price
        self.price_notes = price_notes
        self.time = time
        self.time_notes = time_notes
        self.features = features
        self.notes = notes

    def __str__(self):
        return str({
            'dates': self.dates,
            'bands': ', '.join(b.name for b in self.bands),
            'venue': self.venue,
            'city': self.city,
            'age': self.age,
            'age_notes': self.age_notes,
            'price': self.price,
            'price_notes': self.price_notes,
            'time': self.time,
            'time_notes': self.time_notes,
            'features': self.features,
            'notes': self.notes
        })
