"""Тестовые роли и проверки. Бизнес-логика здесь не реализуется."""
import unittest
from skvoznyak import (Skvoznyak, CrazyVehicleError, SkvoznyakError,
    SkvoznyakAlreadyAirborne, SkvoznyakSailsFolded, SkvoznyakSailsDamaged,
    SkvoznyakBadWind, SkvoznyakOverloaded, SkvoznyakNoEnergy,
    SkvoznyakWrongMedium, SkvoznyakNotAirborne, SkvoznyakRouteLimit,
    SkvoznyakUnsafeOperation)

NONFINITE=(float("nan"),float("inf"),float("-inf"))
BAD_TYPES=(True,False,None,"10",[],{},1+2j)
ATTRS=("name","mass_kg","max_speed_kmh","energy","wind_speed_kmh",
       "position_km","sail_count","working_sails","sails_deployed",
       "is_airborne","lift_capacity_kg","can_takeoff")
FLOATS={"mass_kg","max_speed_kmh","energy","wind_speed_kmh","position_km","lift_capacity_kg"}
DOMAIN_ERRORS=(SkvoznyakAlreadyAirborne,SkvoznyakSailsFolded,SkvoznyakSailsDamaged,
    SkvoznyakBadWind,SkvoznyakOverloaded,SkvoznyakNoEnergy,
    SkvoznyakWrongMedium,SkvoznyakNotAirborne,SkvoznyakRouteLimit,SkvoznyakUnsafeOperation)

def make(**overrides):
    args=dict(name="Сквозняк",mass_kg=200,max_speed_kmh=50)
    args.update(overrides)
    return Skvoznyak(**args)

def flying(**overrides):
    d=make(**overrides)
    d.deploy_sails()
    d.takeoff()
    return d

def damage(d,count):
    for _ in range(count): d.damage_sail()

def snapshot(d):
    # Независим от get_status: ошибка get_status не скроет изменение атрибутов.
    return {key:getattr(d,key) for key in ATTRS}

class ContractCase(unittest.TestCase):
    def number(self,actual,expected):
        self.assertIs(type(actual),float)
        self.assertAlmostEqual(actual,expected,places=6)

    def check(self,d,**expected):
        for key,value in expected.items():
            with self.subTest(attribute=key):
                actual=getattr(d,key)
                if key in FLOATS: self.number(actual,value)
                else:
                    self.assertIs(type(actual),type(value))
                    self.assertEqual(actual,value)

    def reject(self,d,error,action):
        before=snapshot(d)
        with self.assertRaises(error) as context: action()
        self.assertEqual(snapshot(d),before)
        return context.exception

class Pilot:
    def __init__(self,vehicle): self.vehicle=vehicle
    def prepare(self): return self.vehicle.deploy_sails()
    def fold(self): return self.vehicle.fold_sails()
    def takeoff(self): return self.vehicle.takeoff()
    def land(self): return self.vehicle.land()
    def fly(self,km): return self.vehicle.move(km,"air")
    def travel(self,km,medium): return self.vehicle.move(km,medium)
    def can_pass(self,obstacle): return self.vehicle.can_overcome(obstacle)

class Weather:
    def __init__(self,vehicle): self.vehicle=vehicle
    def change(self,speed): return self.vehicle.set_wind(speed)
    def tear(self): return self.vehicle.damage_sail()

class Workshop:
    def __init__(self,vehicle): self.vehicle=vehicle
    def repair(self): return self.vehicle.repair_sails()
    def charge(self,amount): return self.vehicle.recharge(amount)
