from django import forms


class NumbersForm(forms.Form):
    """
    Form with five numeric inputs (a, b, c, d, e).
    Per assignment, inputs must be numeric; negative values are accepted
    but will trigger a warning in the result (not rejected here).
    """

    a = forms.FloatField(label="a", required=True)
    b = forms.FloatField(label="b", required=True)
    c = forms.FloatField(label="c", required=True)
    d = forms.FloatField(label="d", required=True)
    e = forms.FloatField(label="e", required=True)
