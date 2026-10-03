from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class Recinto(models.Model):
    """
    Lugar fisico donde se realiza un evento.

    El recinto se mantiene separado de Evento para evitar
    duplicar informacion como direccion, ciudad y capacidad.
    """

    nombre = models.CharField(
        max_length=150,
        unique=True,
    )

    direccion = models.CharField(
        max_length=200,
    )

    ciudad = models.CharField(
        max_length=100,
    )

    capacidad = models.PositiveIntegerField()

    activo = models.BooleanField(
        default=True,
    )

    creado_en = models.DateTimeField(
        auto_now_add=True,
    )

    actualizado_en = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ("nombre",)
        verbose_name = "recinto"
        verbose_name_plural = "recintos"

    def __str__(self):
        return f"{self.nombre} - {self.ciudad}"


class Evento(models.Model):
    """
    Evento o concierto publicado en el sistema.

    Cada evento pertenece a un recinto y a un usuario
    organizador.

    La modalidad determina si las entradas son generales
    o si requieren seleccionar una ubicacion/asiento.
    """

    class Estado(models.TextChoices):
        BORRADOR = "BORRADOR", "Borrador"
        PUBLICADO = "PUBLICADO", "Publicado"
        CANCELADO = "CANCELADO", "Cancelado"
        FINALIZADO = "FINALIZADO", "Finalizado"

    class ModalidadEntrada(models.TextChoices):
        GENERAL = "GENERAL", "Entrada general / libre"
        UBICACION = "UBICACION", "Entrada con ubicacion"

    nombre = models.CharField(
        max_length=200,
    )

    descripcion = models.TextField()

    imagen = models.ImageField(
        upload_to="eventos/",
        blank=True,
        null=True,
    )

    fecha_inicio = models.DateTimeField()

    fecha_fin = models.DateTimeField()

    recinto = models.ForeignKey(
        Recinto,
        on_delete=models.PROTECT,
        related_name="eventos",
    )

    organizador = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="eventos_organizados",
    )

    estado = models.CharField(
        max_length=20,
        choices=Estado.choices,
        default=Estado.BORRADOR,
    )

    modalidad_entrada = models.CharField(
        max_length=20,
        choices=ModalidadEntrada.choices,
        default=ModalidadEntrada.GENERAL,
    )

    activo = models.BooleanField(
        default=True,
    )

    creado_en = models.DateTimeField(
        auto_now_add=True,
    )

    actualizado_en = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ("fecha_inicio",)
        verbose_name = "evento"
        verbose_name_plural = "eventos"

    def clean(self):
        """
        Validaciones de negocio del evento.
        """

        if self.fecha_inicio and self.fecha_fin:
            if self.fecha_fin <= self.fecha_inicio:
                raise ValidationError(
                    {
                        "fecha_fin": (
                            "La fecha de termino debe ser posterior "
                            "a la fecha de inicio."
                        )
                    }
                )

        if self.organizador_id:
            if self.organizador.rol != "ORGANIZADOR":
                raise ValidationError(
                    {
                        "organizador": (
                            "El usuario seleccionado debe tener "
                            "rol ORGANIZADOR."
                        )
                    }
                )

    def __str__(self):
        return f"{self.nombre} - {self.fecha_inicio:%d-%m-%Y}"


class TipoEntrada(models.Model):
    """
    Categoria de entrada disponible para un evento.

    El stock pertenece al tipo de entrada y no al evento.
    Agregar una entrada al carro NO modifica stock_disponible.
    """

    evento = models.ForeignKey(
        Evento,
        on_delete=models.CASCADE,
        related_name="tipos_entrada",
    )

    nombre = models.CharField(
        max_length=100,
    )

    descripcion = models.CharField(
        max_length=250,
        blank=True,
    )

    precio = models.DecimalField(
        max_digits=10,
        decimal_places=2,
    )

    stock_total = models.PositiveIntegerField()

    stock_disponible = models.PositiveIntegerField()

    activo = models.BooleanField(
        default=True,
    )

    creado_en = models.DateTimeField(
        auto_now_add=True,
    )

    actualizado_en = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ("evento", "precio")
        verbose_name = "tipo de entrada"
        verbose_name_plural = "tipos de entrada"
        constraints = [
            models.UniqueConstraint(
                fields=("evento", "nombre"),
                name="tipo_entrada_nombre_unico_por_evento",
            ),
        ]

    def clean(self):
        """
        Impide que el stock disponible sea superior
        al stock total configurado.
        """

        if (
            self.stock_disponible is not None
            and self.stock_total is not None
            and self.stock_disponible > self.stock_total
        ):
            raise ValidationError(
                {
                    "stock_disponible": (
                        "El stock disponible no puede superar "
                        "el stock total."
                    )
                }
            )

    def __str__(self):
        return f"{self.evento.nombre} - {self.nombre}"


class Locacion(models.Model):
    """
    Sector o ubicacion disponible dentro de un evento
    que utiliza entradas con asiento.
    """

    evento = models.ForeignKey(
        Evento,
        on_delete=models.CASCADE,
        related_name="locaciones",
    )

    tipo_entrada = models.ForeignKey(
        TipoEntrada,
        on_delete=models.PROTECT,
        related_name="locaciones",
        null=True,
        blank=True,
    )

    nombre = models.CharField(
        max_length=100,
    )

    descripcion = models.CharField(
        max_length=250,
        blank=True,
    )

    orden = models.PositiveIntegerField(
        default=1,
    )

    activo = models.BooleanField(
        default=True,
    )

    creado_en = models.DateTimeField(
        auto_now_add=True,
    )

    actualizado_en = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ("evento", "orden", "nombre")
        verbose_name = "locacion"
        verbose_name_plural = "locaciones"
        constraints = [
            models.UniqueConstraint(
                fields=("evento", "nombre"),
                name="locacion_nombre_unico_por_evento",
            ),
        ]

    def clean(self):
        """
        Una locacion solamente puede pertenecer a un evento
        configurado con modalidad de entrada con ubicacion.
        """

        if (
            self.evento_id
            and self.evento.modalidad_entrada
            != Evento.ModalidadEntrada.UBICACION
        ):
            raise ValidationError(
                {
                    "evento": (
                        "Las locaciones solo pueden utilizarse "
                        "en eventos con entrada con ubicacion."
                    )
                }
            )

    def __str__(self):
        return f"{self.evento.nombre} - {self.nombre}"


class Asiento(models.Model):
    """
    Asiento fisico perteneciente a una locacion.
    """

    locacion = models.ForeignKey(
        Locacion,
        on_delete=models.CASCADE,
        related_name="asientos",
    )

    codigo = models.CharField(
        max_length=20,
    )

    fila = models.CharField(
        max_length=10,
        blank=True,
    )

    numero = models.PositiveIntegerField(
        null=True,
        blank=True,
    )

    activo = models.BooleanField(
        default=True,
    )

    creado_en = models.DateTimeField(
        auto_now_add=True,
    )

    actualizado_en = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ("locacion", "fila", "numero", "codigo")
        verbose_name = "asiento"
        verbose_name_plural = "asientos"
        constraints = [
            models.UniqueConstraint(
                fields=("locacion", "codigo"),
                name="asiento_codigo_unico_por_locacion",
            ),
        ]

    def __str__(self):
        return (
            f"{self.locacion.evento.nombre} - "
            f"{self.locacion.nombre} - "
            f"{self.codigo}"
        )
