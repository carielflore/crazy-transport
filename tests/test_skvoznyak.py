"""SPEC v0.1. Модульные тесты AAA."""
from tests.helpers import *


class TestSkvoznyak(ContractCase):
    def test_tc01_init(self):
        """TC-01. Создание и типы. SPEC 3.2–3.3."""
        d = Skvoznyak(" Сквозняк ", 200, 50)
        self.check(d, name=" Сквозняк ", mass_kg=200, max_speed_kmh=50,
                   energy=100, wind_speed_kmh=20, position_km=0, sail_count=6,
                   working_sails=6, sails_deployed=False, is_airborne=False,
                   lift_capacity_kg=300, can_takeoff=False)
        d = make(energy=17, wind_speed_kmh=40)
        self.check(d, energy=17, wind_speed_kmh=40)

    def test_tc02_init_values(self):
        """TC-02. Диапазоны конструктора. SPEC 3.0, 3.2."""
        for name in ("", " ", "\t\n"):
            with self.subTest(name=name), self.assertRaises(ValueError):
                make(name=name)
        for key, lo, hi in (("mass_kg",1,10000),("max_speed_kmh",1,300),
                            ("energy",0,100),("wind_speed_kmh",0,100)):
            for value in (lo, hi):
                with self.subTest(key=key, value=value):
                    self.check(make(**{key:value}), **{key:value})
            for value in (lo-0.1, hi+0.1, *NONFINITE, 10**400, -(10**400)):
                with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                    make(**{key:value})

    def test_tc03_init_types(self):
        """TC-03. Типы и их приоритет. SPEC 3.0, 3.2."""
        for value in (123, None, True, []):
            with self.subTest(name=value), self.assertRaises(TypeError):
                make(name=value)
        for key in ("mass_kg","max_speed_kmh","energy","wind_speed_kmh"):
            for value in BAD_TYPES:
                with self.subTest(key=key,value=value), self.assertRaises(TypeError):
                    make(**{key:value})
        with self.assertRaises(TypeError):
            make(name="", mass_kg="200")
        with self.assertRaises(TypeError):
            make(mass_kg=-1, wind_speed_kmh=None)

    def test_tc04_readonly(self):
        """TC-04. Атрибуты только для чтения. SPEC 3.3."""
        d=make()
        for key,value in snapshot(d).items():
            with self.subTest(key=key):
                self.reject(d, AttributeError, lambda: setattr(d,key,value))

    def test_tc05_sail_controls(self):
        """TC-05. Раскрытие и складывание. SPEC 3.4.1."""
        d=make()
        self.assertIsNone(d.deploy_sails())
        self.check(d, sails_deployed=True, can_takeoff=True, energy=100, position_km=0, is_airborne=False)
        b=snapshot(d); self.assertIsNone(d.deploy_sails()); self.assertEqual(snapshot(d),b)
        self.assertIsNone(d.fold_sails())
        self.check(d,sails_deployed=False,can_takeoff=False,energy=100,position_km=0)
        b=snapshot(d); self.assertIsNone(d.fold_sails()); self.assertEqual(snapshot(d),b)
        damage(d,6); self.assertIsNone(d.deploy_sails())
        self.check(d,working_sails=0,sails_deployed=True,can_takeoff=False)

    def test_tc06_takeoff(self):
        """TC-06. Взлёт и точный бюджет. SPEC 3.4.2."""
        for energy,left in ((100,95),(5,0)):
            with self.subTest(energy=energy):
                d=make(energy=energy); d.deploy_sails()
                self.assertIs(d.can_takeoff,True)
                self.assertIsNone(d.takeoff())
                self.check(d,energy=left,position_km=0,is_airborne=True,
                           sails_deployed=True,working_sails=6,can_takeoff=False)

    def test_tc07_takeoff_priority(self):
        """TC-07. Причины отказа взлёта и границы. SPEC 3.4.2, 6.3."""
        d=make(mass_kg=400,energy=0,wind_speed_kmh=0); damage(d,4)
        self.reject(d,SkvoznyakSailsFolded,d.takeoff)
        d.deploy_sails(); self.reject(d,SkvoznyakSailsDamaged,d.takeoff)
        d.repair_sails(); self.reject(d,SkvoznyakBadWind,d.takeoff)
        d.set_wind(20); self.reject(d,SkvoznyakOverloaded,d.takeoff)
        d=make(energy=4.9); d.deploy_sails()
        e=self.reject(d,SkvoznyakNoEnergy,d.takeoff)
        self.assertEqual((e.required,e.available),(5.0,4.9))
        for wind in (10,60):
            d=make(mass_kg=300,wind_speed_kmh=wind); d.deploy_sails(); d.takeoff()
            self.check(d,is_airborne=True)
        d=make(mass_kg=300.1); d.deploy_sails()
        self.reject(d,SkvoznyakOverloaded,d.takeoff)

    def test_tc08_repeated_takeoff(self):
        """TC-08. Повторный взлёт. SPEC 3.4.2."""
        for energy in (100,5):
            d=flying(energy=energy)
            self.reject(d,SkvoznyakAlreadyAirborne,d.takeoff)

    def test_tc09_can_takeoff(self):
        """TC-09. Матрица готовности. SPEC 3.3."""
        for kwargs,broken,opened,expected in (
            ({},0,False,False),({},0,True,True),({"energy":4.9},0,True,False),
            ({"energy":5},0,True,True),({"wind_speed_kmh":9.9},0,True,False),
            ({"wind_speed_kmh":60.1},0,True,False),({"mass_kg":301},0,True,False),
            ({"mass_kg":100},4,True,False),({"mass_kg":150},3,True,True)):
            with self.subTest(kwargs=kwargs,broken=broken,opened=opened):
                d=make(**kwargs); damage(d,broken)
                if opened: d.deploy_sails()
                b=snapshot(d); self.assertIs(d.can_takeoff,expected); self.assertEqual(snapshot(d),b)

    def test_tc10_land(self):
        """TC-10. Бесплатная посадка. SPEC 3.4.3."""
        for energy in (100,5):
            d=flying(energy=energy); b=snapshot(d)
            self.assertIsNone(d.land())
            b.update(is_airborne=False,can_takeoff=(energy-5>=5))
            self.assertEqual(snapshot(d),b)
            self.assertIsNone(d.land()); self.assertEqual(snapshot(d),b)

    def test_tc11_move_speed(self):
        """TC-11. Скорость, ограничитель и повреждённые паруса. SPEC 3.4.4."""
        for max_speed,broken,hours in ((50,0,0.5),(12,0,10/12),(50,3,1.0)):
            with self.subTest(max_speed=max_speed,broken=broken):
                d=make(mass_kg=150,max_speed_kmh=max_speed); damage(d,broken)
                d.deploy_sails(); d.takeoff()
                self.number(d.move(10,"air"),hours)
                self.check(d,energy=85,position_km=10,is_airborne=True,
                           working_sails=6-broken,wind_speed_kmh=20)

    def test_tc12_storm_threshold(self):
        """TC-12. Обычный и штормовой режим. SPEC 3.4.4."""
        for wind,cost in ((30,10),(30.1,20),(60,20)):
            with self.subTest(wind=wind):
                d=flying(wind_speed_kmh=wind,max_speed_kmh=100)
                self.number(d.move(10,"air"),10/wind)
                self.check(d,energy=95-cost,position_km=10,is_airborne=True)

    def test_tc13_move_validation(self):
        """TC-13. Аргументы движения. SPEC 3.0, 3.4.4."""
        d=flying()
        for value in (0,-1,1000.1,*NONFINITE,10**400):
            self.reject(d,ValueError,lambda: d.move(value,"air"))
        for value in BAD_TYPES:
            self.reject(d,TypeError,lambda: d.move(value,"air"))
        for terrain in ("", "AIR", "space"):
            self.reject(d,ValueError,lambda: d.move(1,terrain))
        for terrain in (123,None,True,[]):
            self.reject(d,TypeError,lambda: d.move(1,terrain))
        self.reject(d,TypeError,lambda: d.move(0,123))
        self.reject(d,ValueError,lambda: d.move(0,"ground"))
        self.reject(d,SkvoznyakNoEnergy,lambda: d.move(1000,"air"))

    def test_tc14_wrong_medium(self):
        """TC-14. Запрет земли и воды. SPEC 3.4.4."""
        for d in (make(energy=0),flying(energy=5)):
            for terrain in ("ground","water"):
                with self.subTest(airborne=d.is_airborne,terrain=terrain):
                    self.reject(d,SkvoznyakWrongMedium,lambda: d.move(1,terrain))

    def test_tc15_not_airborne(self):
        """TC-15. Движение не заменяет взлёт. SPEC 3.4.4."""
        for energy in (0,100):
            d=make(energy=energy); d.deploy_sails()
            self.reject(d,SkvoznyakNotAirborne,lambda: d.move(1,"air"))

    def test_tc16_move_budget(self):
        """TC-16. Точный и недостаточный бюджет. SPEC 3.4.4."""
        for wind,distance in ((20,10),(40,5)):
            d=flying(energy=15,wind_speed_kmh=wind)
            e=self.reject(d,SkvoznyakNoEnergy,lambda: d.move(distance+1,"air"))
            self.number(e.required,(distance+1)*(1 if wind==20 else 2))
            self.number(e.available,10)
            d.move(distance,"air")
            self.check(d,energy=0,position_km=distance,is_airborne=True)
            self.reject(d,SkvoznyakNoEnergy,lambda: d.move(1,"air"))

    def test_tc17_calculate_pure(self):
        """TC-17. Расчёт без проверки возможности полёта. SPEC 3.4.5."""
        for wind,cost in ((0,1000),(30,1000),(40,2000),(100,2000)):
            d=make(mass_kg=400,energy=0,wind_speed_kmh=wind); damage(d,6)
            b=snapshot(d)
            self.number(d.calculate_energy(1000,"air"),cost)
            self.assertEqual(snapshot(d),b)

    def test_tc18_calculate_validation(self):
        """TC-18. Аргументы расчёта. SPEC 3.0, 3.4.5."""
        d=make()
        for value in (0,-1,1000.1,*NONFINITE,10**400):
            self.reject(d,ValueError,lambda: d.calculate_energy(value,"air"))
        for value in BAD_TYPES:
            self.reject(d,TypeError,lambda: d.calculate_energy(value,"air"))
        for value in (None,123,True,[]):
            self.reject(d,TypeError,lambda: d.calculate_energy(1,value))
        for value in ("", "AIR", "space"):
            self.reject(d,ValueError,lambda: d.calculate_energy(1,value))
        for value in ("ground","water"):
            self.reject(d,SkvoznyakWrongMedium,lambda: d.calculate_energy(1,value))
        self.reject(d,TypeError,lambda: d.calculate_energy(0,123))
        self.reject(d,ValueError,lambda: d.calculate_energy(0,"water"))

    def test_tc19_wind_event(self):
        """TC-19. Смена ветра и аварийная посадка. SPEC 3.4.6."""
        for wind,stays in ((10,True),(60,True),(0,False),(9.9,False),(60.1,False),(100,False)):
            with self.subTest(wind=wind):
                d=flying(); b=snapshot(d)
                self.assertIsNone(d.set_wind(wind))
                b.update(wind_speed_kmh=float(wind),is_airborne=stays)
                self.assertEqual(snapshot(d),b)
                d.set_wind(20)
                self.check(d,is_airborne=stays,can_takeoff=not stays)

    def test_tc20_wind_invalid(self):
        """TC-20. Неверный ветер не вызывает посадку. SPEC 3.0, 3.4.6."""
        d=flying()
        for value in BAD_TYPES:
            self.reject(d,TypeError,lambda: d.set_wind(value))
        for value in (-0.1,100.1,*NONFINITE,10**400):
            self.reject(d,ValueError,lambda: d.set_wind(value))

    def test_tc21_damage_mass(self):
        """TC-21. Потеря несущей способности. SPEC 3.4.7."""
        d=flying(); d.move(10,"air")
        for count,airborne in ((5,True),(4,True),(3,False)):
            self.assertIsNone(d.damage_sail())
            self.check(d,working_sails=count,lift_capacity_kg=count*50,
                       is_airborne=airborne,energy=85,position_km=10,
                       sails_deployed=True,can_takeoff=False)

    def test_tc22_damage_minimum(self):
        """TC-22. Минимум три паруса. SPEC 3.4.7."""
        d=flying(mass_kg=100); damage(d,3)
        self.check(d,working_sails=3,lift_capacity_kg=150,is_airborne=True)
        d.damage_sail()
        self.check(d,working_sails=2,lift_capacity_kg=100,is_airborne=False,energy=95,position_km=0)

    def test_tc23_damage_floor(self):
        """TC-23. Нижняя граница числа парусов. SPEC 3.4.7."""
        d=make(); damage(d,6)
        self.check(d,working_sails=0,lift_capacity_kg=0,can_takeoff=False,energy=100,position_km=0)
        b=snapshot(d); self.assertIsNone(d.damage_sail()); self.assertEqual(snapshot(d),b)

    def test_tc24_repair(self):
        """TC-24. Ремонт и запрет ремонта в воздухе. SPEC 3.4.8."""
        d=make(); d.deploy_sails(); damage(d,4); b=snapshot(d)
        self.assertIsNone(d.repair_sails())
        b.update(working_sails=6,lift_capacity_kg=300.0,can_takeoff=True)
        self.assertEqual(snapshot(d),b)
        self.assertIsNone(d.repair_sails()); self.assertEqual(snapshot(d),b)
        for broken in (0,1):
            d=flying(); damage(d,broken)
            self.reject(d,SkvoznyakUnsafeOperation,d.repair_sails)

    def test_tc25_fold_in_air(self):
        """TC-25. Запрет складывания в полёте. SPEC 3.4.1."""
        d=flying(energy=5)
        self.reject(d,SkvoznyakUnsafeOperation,d.fold_sails)
        b=snapshot(d); self.assertIsNone(d.deploy_sails()); self.assertEqual(snapshot(d),b)

    def test_tc26_recharge(self):
        """TC-26. Зарядка на земле и потолок. SPEC 3.4.9."""
        for start,amount,end in ((20,50,70),(50,1000,100),(100,0.5,100)):
            d=make(energy=start); b=snapshot(d)
            self.assertIsNone(d.recharge(amount)); b.update(energy=float(end))
            self.assertEqual(snapshot(d),b)
        d=flying(energy=5)
        self.reject(d,SkvoznyakUnsafeOperation,lambda: d.recharge(10))

    def test_tc27_recharge_invalid(self):
        """TC-27. Проверки зарядки раньше положения. SPEC 3.0, 3.4.9."""
        for d in (make(),flying()):
            for value in BAD_TYPES:
                self.reject(d,TypeError,lambda: d.recharge(value))
            for value in (0,-1,1000.1,*NONFINITE,10**400):
                self.reject(d,ValueError,lambda: d.recharge(value))

    def test_tc28_obstacle_matrix(self):
        """TC-28. Матрица препятствий. SPEC 3.4.10."""
        cases=[(make(),(False,False,False)),(flying(),(True,True,False)),
               (flying(wind_speed_kmh=30),(True,True,False)),
               (flying(wind_speed_kmh=40),(True,True,True)),
               (flying(energy=5,wind_speed_kmh=40),(False,False,False))]
        for broken,expected in ((1,(True,True,False)),(2,(True,False,False))):
            d=flying(wind_speed_kmh=40); damage(d,broken); cases.append((d,expected))
        for d,expected in cases:
            b=snapshot(d)
            for obstacle,result in zip(("canyon","ridge","storm_front"),expected):
                self.assertIs(d.can_overcome(obstacle),result)
            self.assertEqual(snapshot(d),b)

    def test_tc29_obstacle_invalid(self):
        """TC-29. Аргументы препятствий. SPEC 3.4.10."""
        d=make()
        for value in (123,None,True,[]):
            self.reject(d,TypeError,lambda: d.can_overcome(value))
        for value in ("", "CANYON", "wall"):
            self.reject(d,ValueError,lambda: d.can_overcome(value))

    def test_tc30_status(self):
        """TC-30. Снимок состояния. SPEC 3.4.11."""
        d=flying(); d.move(10,"air"); before=snapshot(d)
        a=d.get_status(); b=d.get_status()
        expected=dict(name="Сквозняк",energy=85.0,position_km=10.0,wind_speed_kmh=20.0,
                      working_sails=6,sails_deployed=True,is_airborne=True,can_takeoff=False)
        self.assertIs(type(a),dict); self.assertEqual(a,expected); self.assertIsNot(a,b)
        for key,value in expected.items(): self.assertIs(type(a[key]),type(value))
        a["energy"]=0; a["is_airborne"]=False; a["extra"]=123
        self.assertEqual(b,expected); self.assertEqual(d.get_status(),expected)
        self.assertEqual(snapshot(d),before)

    def test_tc31_exceptions(self):
        """TC-31. Иерархия и поля исключения. SPEC 6.1–6.2."""
        self.assertTrue(issubclass(CrazyVehicleError,Exception))
        self.assertTrue(issubclass(SkvoznyakError,CrazyVehicleError))
        for cls in DOMAIN_ERRORS:
            self.assertTrue(issubclass(cls,SkvoznyakError))
            if cls is not SkvoznyakNoEnergy: self.assertIsInstance(cls("причина"),Exception)
        for e,r,a in ((SkvoznyakNoEnergy(6,2),6,2),
                      (SkvoznyakNoEnergy(required=7,available=3),7,3)):
            self.number(e.required,r); self.number(e.available,a)

    def test_tc32_route_limit(self):
        """TC-32. Граница суммарного пути. SPEC 3.4.4–3.4.5."""
        d=flying()
        # Каждый участок 100 км начинается с полным аккумулятором.
        for _ in range(100):
            d.land(); d.recharge(100); d.takeoff()
            d.move(95,"air")
            d.land(); d.recharge(10); d.takeoff(); d.move(5,"air")
        self.check(d,position_km=10000,energy=0,is_airborne=True)
        self.reject(d,SkvoznyakRouteLimit,lambda: d.move(1,"air"))
        self.reject(d,SkvoznyakWrongMedium,lambda: d.move(1,"water"))
        self.reject(d,TypeError,lambda: d.move(0,None))
        b=snapshot(d); self.number(d.calculate_energy(1,"air"),1); self.assertEqual(snapshot(d),b)
        d.land(); self.reject(d,SkvoznyakNotAirborne,lambda: d.move(1,"air"))


if __name__ == "__main__":
    unittest.main()
