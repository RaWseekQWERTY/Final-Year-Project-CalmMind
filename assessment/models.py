from django.db import models
from django.utils.timezone import now

class PHQ9Assessment(models.Model):
    DEPRESSION_LEVELS = [
        ('0', 'No Depression'),
        ('1', 'Low Depression'),
        ('2', 'Mild Depression'),
        ('3', 'Severe Depression'),
    ]
    
    assessment_id = models.AutoField(primary_key=True)
    patient = models.ForeignKey('auth_app.Patient', on_delete=models.CASCADE)
    
    # Individual question scores (0–3)
    q1 = models.PositiveSmallIntegerField()
    q2 = models.PositiveSmallIntegerField()
    q3 = models.PositiveSmallIntegerField()
    q4 = models.PositiveSmallIntegerField()
    q5 = models.PositiveSmallIntegerField()
    q6 = models.PositiveSmallIntegerField()
    q7 = models.PositiveSmallIntegerField()
    q8 = models.PositiveSmallIntegerField()
    q9 = models.PositiveSmallIntegerField()
    
    # Actual assessment results
    score = models.PositiveSmallIntegerField()
    depression_level = models.CharField(max_length=1, choices=DEPRESSION_LEVELS)
    
    # Predicted results from multi-output classifier
    predicted_score = models.PositiveSmallIntegerField(null=True, blank=True)
    predicted_depression_level = models.CharField(max_length=1, choices=DEPRESSION_LEVELS, null=True, blank=True)
    
    assessment_date = models.DateField(default=now)
    
    def save(self, *args, **kwargs):
        """Calculate total score and assign depression level before saving."""
        self.score = sum([self.q1, self.q2, self.q3, self.q4, self.q5, 
                          self.q6, self.q7, self.q8, self.q9])
        
        # Assign depression level based on score
        if self.score <= 4:
            self.depression_level = '0'  # No Depression
        elif 5 <= self.score <= 9:
            self.depression_level = '1'  # Low Depression
        elif 10 <= self.score <= 14:
            self.depression_level = '2'  # Mild Depression
        else:
            self.depression_level = '3'  # Severe Depression
        
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Assessment {self.assessment_id} - Patient {self.patient_id} - Score: {self.score}"
