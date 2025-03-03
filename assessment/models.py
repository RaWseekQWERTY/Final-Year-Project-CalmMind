from django.db import models
from django.utils.timezone import now

class PHQ9Assessment(models.Model):
    DEPRESSION_LEVELS = [
        ('0', 'None'),
        ('1', 'Mild'),
        ('2', 'Moderate'),
        ('3', 'Moderately Severe'),
        ('4', 'Severe'),
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
    q10 = models.PositiveSmallIntegerField(default=0)
    
    # Actual assessment results
    score = models.PositiveSmallIntegerField()
    depression_level = models.CharField(max_length=1, choices=DEPRESSION_LEVELS)
    
    # Predicted results from multi-output classifier
    predicted_score = models.PositiveSmallIntegerField(null=True, blank=True)
    predicted_depression_level = models.CharField(max_length=1, choices=DEPRESSION_LEVELS, null=True, blank=True)
    
    assessment_date = models.DateTimeField(auto_now_add=True)
    
    def save(self, *args, **kwargs):
        """Calculate total score and assign depression level before saving."""
        self.score = sum([self.q1, self.q2, self.q3, self.q4, self.q5, 
                          self.q6, self.q7, self.q8, self.q9])
        
        # Assign depression level based on the updated 5-class PHQ-9 ranges
        if self.score <= 4:
            self.depression_level = '0'  # None
        elif 5 <= self.score <= 9:
            self.depression_level = '1'  # Mild
        elif 10 <= self.score <= 14:
            self.depression_level = '2'  # Moderate
        elif 15 <= self.score <= 19:
            self.depression_level = '3'  # Moderately Severe
        else:
            self.depression_level = '4'  # Severe
        
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Assessment {self.assessment_id} - Patient {self.patient_id} - Score: {self.score}"
