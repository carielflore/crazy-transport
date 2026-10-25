"""SPEC v0.1. Сценарные тесты GWT."""
from tests.helpers import *


class TestScenarios(ContractCase):
    def test_tc33_delivery(self):
        """TC-33. Доставка через бурю. SPEC 4.2."""
        # Given: пилот и эталонный парусник.
        d=make(); p=Pilot(d); w=Weather(d)
        # When / Then: обычный участок.
        p.prepare(); p.takeoff(); self.number(p.fly(10),0.5)
        self.check(d,energy=85,position_km=10,is_airborne=True)
        # When / Then: штормовой участок и прибытие.
        w.change(40); self.assertIs(p.can_pass("storm_front"),True)
        self.number(p.fly(20),0.5)
        p.land(); p.fold()
        self.check(d,energy=45,position_km=30,is_airborne=False,sails_deployed=False)

    def test_tc34_calm(self):
        """TC-34. Ветер исчез. SPEC 4.2."""
        # Given
        d=make(wind_speed_kmh=0); p=Pilot(d); w=Weather(d); p.prepare()
        # When / Then
        self.reject(d,SkvoznyakBadWind,p.takeoff)
        w.change(20); p.takeoff(); p.fly(10)
        w.change(0)
        self.check(d,is_airborne=False,energy=85,position_km=10,sails_deployed=True)
        self.reject(d,SkvoznyakNotAirborne,lambda:p.fly(1))
        w.change(20); self.check(d,is_airborne=False,can_takeoff=True)
        p.takeoff(); self.number(p.fly(5),0.25)
        self.check(d,is_airborne=True,energy=75,position_km=15)

    def test_tc35_storm_limit(self):
        """TC-35. Оседлать бурю. SPEC 4.2."""
        # Given
        d=make(wind_speed_kmh=30,max_speed_kmh=100); p=Pilot(d); w=Weather(d)
        # When / Then
        p.prepare(); p.takeoff(); self.number(p.fly(10),1/3)
        self.check(d,energy=85)
        w.change(60); self.number(p.fly(15),0.25)
        self.check(d,energy=55,position_km=25)
        w.change(60.1); self.check(d,is_airborne=False)
        self.reject(d,SkvoznyakBadWind,p.takeoff)
        w.change(40); p.takeoff(); self.number(p.fly(10),0.25)
        self.check(d,energy=30,position_km=35,is_airborne=True)

    def test_tc36_torn_sails(self):
        """TC-36. Паруса не выдержали. SPEC 4.2."""
        # Given
        d=make(); p=Pilot(d); w=Weather(d); shop=Workshop(d)
        # When / Then
        p.prepare(); p.takeoff(); p.fly(10)
        w.tear(); self.number(p.fly(10),0.6)
        self.check(d,working_sails=5,energy=75,position_km=20)
        w.tear(); self.check(d,working_sails=4,is_airborne=True,lift_capacity_kg=200)
        w.tear(); self.check(d,working_sails=3,is_airborne=False,energy=75,position_km=20)
        self.reject(d,SkvoznyakOverloaded,p.takeoff)
        shop.repair(); self.check(d,working_sails=6,is_airborne=False)
        p.takeoff(); p.fly(10)
        self.check(d,energy=60,position_km=30,is_airborne=True)

    def test_tc37_last_charge(self):
        """TC-37. Последний заряд. SPEC 4.2."""
        # Given
        d=make(energy=5); p=Pilot(d); shop=Workshop(d)
        # When / Then
        p.prepare(); p.takeoff(); self.check(d,energy=0,is_airborne=True)
        self.assertIs(p.can_pass("canyon"),False)
        e=self.reject(d,SkvoznyakNoEnergy,lambda:p.fly(1))
        self.number(e.required,1); self.number(e.available,0)
        self.reject(d,SkvoznyakUnsafeOperation,lambda:shop.charge(15))
        p.land(); shop.charge(15); p.takeoff(); p.fly(10)
        self.check(d,energy=0,position_km=10,is_airborne=True)
        p.land(); self.check(d,is_airborne=False,energy=0,can_takeoff=False)

    def test_tc38_three_sails(self):
        """TC-38. На трёх парусах. SPEC 4.2."""
        # Given
        d=make(mass_kg=150); p=Pilot(d); w=Weather(d); shop=Workshop(d)
        # When / Then
        for _ in range(3): w.tear()
        p.prepare(); self.check(d,can_takeoff=True,lift_capacity_kg=150)
        p.takeoff(); self.number(p.fly(20),2)
        self.assertIs(p.can_pass("canyon"),True); self.assertIs(p.can_pass("ridge"),False)
        w.tear(); self.check(d,is_airborne=False,working_sails=2)
        self.reject(d,SkvoznyakSailsDamaged,p.takeoff)
        shop.repair()
        self.check(d,energy=75,position_km=20,working_sails=6,is_airborne=False,can_takeoff=True)

    def test_tc39_wrong_routes(self):
        """TC-39. Через реку только по воздуху. SPEC 4.2."""
        # Given
        d=make(); p=Pilot(d)
        # When / Then
        self.reject(d,SkvoznyakWrongMedium,lambda:p.travel(1,"ground"))
        p.prepare(); p.takeoff(); p.fly(5)
        self.reject(d,SkvoznyakWrongMedium,lambda:p.travel(1,"water"))
        self.assertIs(p.can_pass("canyon"),True)
        p.fly(5); p.land()
        self.check(d,energy=85,position_km=10,is_airborne=False)
        self.reject(d,SkvoznyakNotAirborne,lambda:p.fly(1))

    def test_tc40_service(self):
        """TC-40. Починка между рейсами. SPEC 4.2."""
        # Given
        d=make(mass_kg=300,energy=20); p=Pilot(d); w=Weather(d); shop=Workshop(d)
        # When / Then
        p.prepare(); p.takeoff(); p.fly(10)
        w.tear(); self.check(d,energy=5,position_km=10,is_airborne=False,working_sails=5)
        p.fold(); shop.repair(); shop.charge(1000)
        self.check(d,energy=100,working_sails=6,sails_deployed=False,can_takeoff=False)
        self.reject(d,SkvoznyakSailsFolded,p.takeoff)
        p.prepare(); p.takeoff(); p.fly(20)
        self.check(d,energy=75,position_km=30,is_airborne=True)


if __name__ == "__main__":
    unittest.main()
