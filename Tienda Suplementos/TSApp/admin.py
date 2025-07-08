from django.contrib import admin
from TSApp.models import Suplementos,Categoria

class SuplementosAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'categoria' , 'descripcion' , 'precio' , 'disponibilidad' , 'oferta' , 'unidadesVendidas' , 'imagenes', 'ofertaPorcentaje']

admin.site.register(Suplementos, SuplementosAdmin)
admin.site.register(Categoria)

