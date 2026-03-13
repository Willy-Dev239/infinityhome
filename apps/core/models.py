# apps/core/models.py  

from django.db import models


class ContactMessage(models.Model):
    nom         = models.CharField(max_length=150)
    email       = models.EmailField()
    commentaire = models.TextField()
    date        = models.DateTimeField(auto_now_add=True)
    lu          = models.BooleanField(default=False)

    class Meta:
        ordering = ['-date']
        verbose_name = 'Message de contact'
        verbose_name_plural = 'Messages de contact'

    def __str__(self):
        return f"{self.nom} — {self.date.strftime('%d/%m/%Y %H:%M')}"