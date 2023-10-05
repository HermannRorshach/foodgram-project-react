from django.core.exceptions import ValidationError
from django.forms.models import BaseInlineFormSet


class IngredientInRecipeFormSetValidator(BaseInlineFormSet):

    def clean(self):
        super().clean()
        if all([form.cleaned_data.get('DELETE')
                for form in self.forms if hasattr(form, 'cleaned_data')]):
            raise ValidationError('Добавьте ингредиент')
