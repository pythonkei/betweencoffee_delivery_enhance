from django import forms # import forms module, this is default, can change css???

'''
商品添加到购物车的逻辑: 用于添加或更新商品
quantity 字段允许用户选择要添加的商品数量（1 到 100）。

override 字段是一个隐藏字段，可能用于控制是否覆盖购物车中已有的数量（如果商品已经在购物车中）。

'''

PRODUCT_QUANTITY_CHOICES = [(i, str(i)) for i in range(1, 101)]

class CartAddItemForm(forms.Form):
    quantity = forms.TypedChoiceField(
                                choices=PRODUCT_QUANTITY_CHOICES,
                                coerce=int)
    override = forms.BooleanField(required=False,
                                  initial=False,
                                  widget=forms.HiddenInput)