from apps.fleet.models import Car, CarCategory


class CarService:
    @staticmethod
    def create_category(*, name: str, slug: str, description: str = "") -> CarCategory:
        return CarCategory.objects.create(
            name=name,
            slug=slug,
            description=description,
        )

    @staticmethod
    def create_car(**kwargs) -> Car:
        return Car.objects.create(**kwargs)

    @staticmethod
    def update_car(car: Car, **kwargs) -> Car:
        for field, value in kwargs.items():
            setattr(car, field, value)
        car.save()
        return car
