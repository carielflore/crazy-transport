"""Запускаемый пример полёта небесного парусника «Сквозняк»."""

from skvoznyak import Skvoznyak


def show_status(stage: str, ship: Skvoznyak) -> None:
    status = ship.get_status()
    location = "в воздухе" if status["is_airborne"] else "на земле"
    sails = "раскрыты" if status["sails_deployed"] else "сложены"
    print(
        f"{stage}: {location}, паруса {sails}, "
        f"энергия {status['energy']:.1f}, путь {status['position_km']:.1f} км, "
        f"ветер {status['wind_speed_kmh']:.1f} км/ч"
    )


def main() -> None:
    ship = Skvoznyak("Сквозняк", mass_kg=200, max_speed_kmh=50)
    show_status("Создание", ship)

    ship.deploy_sails()
    ship.takeoff()
    show_status("Взлёт", ship)

    flight_time = ship.move(10, "air")
    print(f"Обычный полёт: 10 км за {flight_time:.2f} ч")
    show_status("После первого участка", ship)

    ship.set_wind(40)
    flight_time = ship.move(20, "air")
    print(f"Полёт в бурю: 20 км за {flight_time:.2f} ч")
    show_status("После второго участка", ship)

    ship.land()
    ship.fold_sails()
    ship.recharge(30)
    show_status("Посадка и зарядка", ship)


if __name__ == "__main__":
    main()
