"""Небесный парусник «Сквозняк» по контракту SPEC 0.1.2."""

import math


__all__ = [
    "CrazyVehicleError",
    "SkvoznyakError",
    "SkvoznyakAlreadyAirborne",
    "SkvoznyakSailsFolded",
    "SkvoznyakSailsDamaged",
    "SkvoznyakBadWind",
    "SkvoznyakOverloaded",
    "SkvoznyakNoEnergy",
    "SkvoznyakWrongMedium",
    "SkvoznyakNotAirborne",
    "SkvoznyakRouteLimit",
    "SkvoznyakUnsafeOperation",
    "Skvoznyak",
]


class CrazyVehicleError(Exception):
    """Базовое исключение безумного транспорта."""


class SkvoznyakError(CrazyVehicleError):
    """Базовое исключение парусника «Сквозняк»."""


class SkvoznyakAlreadyAirborne(SkvoznyakError):
    """Парусник уже находится в воздухе."""


class SkvoznyakSailsFolded(SkvoznyakError):
    """Паруса не раскрыты."""


class SkvoznyakSailsDamaged(SkvoznyakError):
    """Исправных парусов недостаточно для взлёта."""


class SkvoznyakBadWind(SkvoznyakError):
    """Ветер не входит в допустимый для взлёта диапазон."""


class SkvoznyakOverloaded(SkvoznyakError):
    """Масса превышает текущую несущую способность."""


class SkvoznyakNoEnergy(SkvoznyakError):
    """Запаса энергии недостаточно для действия."""

    def __init__(self, required: float, available: float) -> None:
        self.required = float(required)
        self.available = float(available)
        super().__init__(
            f"Требуется энергии: {self.required}; доступно: {self.available}"
        )


class SkvoznyakWrongMedium(SkvoznyakError):
    """Выбрана неподдерживаемая среда движения."""


class SkvoznyakNotAirborne(SkvoznyakError):
    """Воздушное движение запрошено на земле."""


class SkvoznyakRouteLimit(SkvoznyakError):
    """Движение превысит предельный суммарный путь."""


class SkvoznyakUnsafeOperation(SkvoznyakError):
    """Действие небезопасно выполнять в воздухе."""


def _require_number(value: object, parameter: str) -> None:
    if type(value) not in (int, float):
        raise TypeError(f"{parameter} должен быть числом")


def _number_in_range(
    value: object, parameter: str, minimum: float, maximum: float
) -> float:
    if type(value) is float and not math.isfinite(value):
        raise ValueError(f"{parameter} должен быть конечным числом")
    if value < minimum or value > maximum:
        raise ValueError(f"{parameter} вне допустимого диапазона")
    return float(value)


def _validate_route(distance_km: object, terrain: object) -> float:
    _require_number(distance_km, "distance_km")
    if type(terrain) is not str:
        raise TypeError("terrain должен быть строкой")

    distance = _number_in_range(distance_km, "distance_km", 0.0, 1000.0)
    if distance == 0.0:
        raise ValueError("distance_km должен быть больше нуля")
    if terrain not in ("air", "ground", "water"):
        raise ValueError("неизвестная среда движения")
    if terrain != "air":
        raise SkvoznyakWrongMedium("движение возможно только по воздуху")
    return distance


class Skvoznyak:
    """Детерминированная модель небесного парусника."""

    __slots__ = (
        "_name",
        "_mass_kg",
        "_max_speed_kmh",
        "_energy",
        "_wind_speed_kmh",
        "_position_km",
        "_working_sails",
        "_sails_deployed",
        "_is_airborne",
    )

    SAIL_COUNT = 6
    MIN_WORKING_SAILS = 3
    LIFT_PER_SAIL_KG = 50.0
    MIN_FLIGHT_WIND_KMH = 10.0
    MAX_FLIGHT_WIND_KMH = 60.0
    STORM_WIND_KMH = 30.0
    TAKEOFF_ENERGY = 5.0
    MAX_ENERGY = 100.0
    MAX_ROUTE_KM = 10000.0

    def __init__(
        self,
        name: str,
        mass_kg: float,
        max_speed_kmh: float,
        energy: float = 100.0,
        wind_speed_kmh: float = 20.0,
    ) -> None:
        if type(name) is not str:
            raise TypeError("name должен быть строкой")
        for value, parameter in (
            (mass_kg, "mass_kg"),
            (max_speed_kmh, "max_speed_kmh"),
            (energy, "energy"),
            (wind_speed_kmh, "wind_speed_kmh"),
        ):
            _require_number(value, parameter)

        if not name.strip():
            raise ValueError("name должен содержать непробельный символ")
        mass = _number_in_range(mass_kg, "mass_kg", 1.0, 10000.0)
        max_speed = _number_in_range(
            max_speed_kmh, "max_speed_kmh", 1.0, 300.0
        )
        initial_energy = _number_in_range(energy, "energy", 0.0, 100.0)
        wind = _number_in_range(
            wind_speed_kmh, "wind_speed_kmh", 0.0, 100.0
        )

        self._name = name
        self._mass_kg = mass
        self._max_speed_kmh = max_speed
        self._energy = initial_energy
        self._wind_speed_kmh = wind
        self._position_km = 0.0
        self._working_sails = self.SAIL_COUNT
        self._sails_deployed = False
        self._is_airborne = False

    @property
    def name(self) -> str:
        return self._name

    @property
    def mass_kg(self) -> float:
        return self._mass_kg

    @property
    def max_speed_kmh(self) -> float:
        return self._max_speed_kmh

    @property
    def energy(self) -> float:
        return self._energy

    @property
    def wind_speed_kmh(self) -> float:
        return self._wind_speed_kmh

    @property
    def position_km(self) -> float:
        return self._position_km

    @property
    def sail_count(self) -> int:
        return self.SAIL_COUNT

    @property
    def working_sails(self) -> int:
        return self._working_sails

    @property
    def sails_deployed(self) -> bool:
        return self._sails_deployed

    @property
    def is_airborne(self) -> bool:
        return self._is_airborne

    @property
    def lift_capacity_kg(self) -> float:
        return self._working_sails * self.LIFT_PER_SAIL_KG

    @property
    def can_takeoff(self) -> bool:
        return (
            not self._is_airborne
            and self._sails_deployed
            and self._working_sails >= self.MIN_WORKING_SAILS
            and self.MIN_FLIGHT_WIND_KMH
            <= self._wind_speed_kmh
            <= self.MAX_FLIGHT_WIND_KMH
            and self._mass_kg <= self.lift_capacity_kg
            and self._energy >= self.TAKEOFF_ENERGY
        )

    def deploy_sails(self) -> None:
        self._sails_deployed = True

    def fold_sails(self) -> None:
        if self._is_airborne:
            raise SkvoznyakUnsafeOperation("нельзя складывать паруса в воздухе")
        self._sails_deployed = False

    def takeoff(self) -> None:
        if self._is_airborne:
            raise SkvoznyakAlreadyAirborne("парусник уже в воздухе")
        if not self._sails_deployed:
            raise SkvoznyakSailsFolded("паруса сложены")
        if self._working_sails < self.MIN_WORKING_SAILS:
            raise SkvoznyakSailsDamaged("исправных парусов меньше трёх")
        if not (
            self.MIN_FLIGHT_WIND_KMH
            <= self._wind_speed_kmh
            <= self.MAX_FLIGHT_WIND_KMH
        ):
            raise SkvoznyakBadWind("ветер не подходит для взлёта")
        if self._mass_kg > self.lift_capacity_kg:
            raise SkvoznyakOverloaded("масса превышает несущую способность")
        if self._energy < self.TAKEOFF_ENERGY:
            raise SkvoznyakNoEnergy(self.TAKEOFF_ENERGY, self._energy)

        self._energy -= self.TAKEOFF_ENERGY
        self._is_airborne = True

    def land(self) -> None:
        self._is_airborne = False

    def move(self, distance_km: float, terrain: str) -> float:
        distance = _validate_route(distance_km, terrain)
        if not self._is_airborne:
            raise SkvoznyakNotAirborne("парусник находится на земле")
        if self._position_km + distance > self.MAX_ROUTE_KM:
            raise SkvoznyakRouteLimit("превышен предел суммарного пути")

        required = self._energy_cost(distance)
        if required > self._energy:
            raise SkvoznyakNoEnergy(required, self._energy)

        speed_kmh = min(
            self._max_speed_kmh,
            self._wind_speed_kmh * (self._working_sails / 6.0),
        )
        self._energy -= required
        self._position_km += distance
        return float(distance / speed_kmh)

    def calculate_energy(self, distance_km: float, terrain: str) -> float:
        distance = _validate_route(distance_km, terrain)
        return self._energy_cost(distance)

    def set_wind(self, speed_kmh: float) -> None:
        _require_number(speed_kmh, "speed_kmh")
        wind = _number_in_range(speed_kmh, "speed_kmh", 0.0, 100.0)
        self._wind_speed_kmh = wind
        if self._is_airborne and not (
            self.MIN_FLIGHT_WIND_KMH <= wind <= self.MAX_FLIGHT_WIND_KMH
        ):
            self._is_airborne = False

    def damage_sail(self) -> None:
        if self._working_sails == 0:
            return

        self._working_sails -= 1
        if self._is_airborne and (
            self._working_sails < self.MIN_WORKING_SAILS
            or self._mass_kg > self.lift_capacity_kg
        ):
            self._is_airborne = False

    def repair_sails(self) -> None:
        if self._is_airborne:
            raise SkvoznyakUnsafeOperation("нельзя ремонтировать паруса в воздухе")
        self._working_sails = self.SAIL_COUNT

    def recharge(self, amount: float) -> None:
        _require_number(amount, "amount")
        charge = _number_in_range(amount, "amount", 0.0, 1000.0)
        if charge == 0.0:
            raise ValueError("amount должен быть больше нуля")
        if self._is_airborne:
            raise SkvoznyakUnsafeOperation("нельзя заряжаться в воздухе")
        self._energy = min(self.MAX_ENERGY, self._energy + charge)

    def can_overcome(self, obstacle: str) -> bool:
        if type(obstacle) is not str:
            raise TypeError("obstacle должен быть строкой")
        if obstacle not in ("canyon", "ridge", "storm_front"):
            raise ValueError("неизвестное препятствие")
        if not self._is_airborne or self._energy <= 0.0:
            return False
        if obstacle == "canyon":
            return True
        if obstacle == "ridge":
            return self._working_sails >= 5
        return (
            self._working_sails == self.SAIL_COUNT
            and self._wind_speed_kmh > self.STORM_WIND_KMH
        )

    def get_status(self) -> dict:
        return {
            "name": self._name,
            "energy": self._energy,
            "position_km": self._position_km,
            "wind_speed_kmh": self._wind_speed_kmh,
            "working_sails": self._working_sails,
            "sails_deployed": self._sails_deployed,
            "is_airborne": self._is_airborne,
            "can_takeoff": self.can_takeoff,
        }

    def _energy_cost(self, distance_km: float) -> float:
        multiplier = 1.0 if self._wind_speed_kmh <= self.STORM_WIND_KMH else 2.0
        return float(distance_km * multiplier)
