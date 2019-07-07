# -*- coding: utf-8 -*-
"""
Created on Wed Jun 26 14:20:02 2019

@author: HaanRJ
"""


from numpy import sqrt

class Costs():  
    def __init__(self):
        super(Costs, self).__init__()
        self.acqi_m2 = None
        self.acqi_type = None
        self.demo_type = None
        self.floodplain_lowering_m2 = None
        self.sidechannel_m3 = None
        self.minor_embankment_m3 = None
        self.roughness_smooth_m3 = None
        self.structures_m = None
        self.dike_m = None
        self.total_costs = None
        self.hexagon_height = None
        self.hexagon_area = None
        self.set_variables()

    def set_variables(self):
        self.acqi_m2 = {
                "agriculture": 6.7,
                "nature": 1.2,
                "water": 0.8,
                "build_envi": 190
                }
        self.acqi_type = {
                "house": 500000,
                "farm": 900000,
                "business": 1400000
                }
        self.demo_type = {
                "house": 20000,
                "farm": 40000,
                "business": 120000
                }
        self.floodplain_lowering_m3 = {
                "storage": 7.2,
                "polluted": 10.2,
                "local_use": 3.1
                }
        self.sidechannel_m3 = {
                "storage": 8.1,
                "polluted": 10.2,
                "local_use": 3.1
                }
        self.minor_embankment_m3 = {
                "storage": 6.9,
                "polluted": 10.2,
                "local_use": 3.1
                }
        self.roughness_smooth_m2 = {
                "grass": 0.054,
                "herbaceous": 0.081,
                "forest": 0.133
                }
        self.structures_m = {
                "lower": 650,
                "ltd": 1900
                }
        self.dike_m = {
                "raise": 3550,
                "relocate": 4400
                }
        self.total_costs = 0
        self.hexagon_height = 250
        a = (2 / sqrt(3)) * (self.hexagon_height / 2)
        self.hexagon_area = ((3 * sqrt(3)) / 2) * (a * a)
        return  

    def calc_Costs(self, hexagon_new, hexagon_old, z_changed=False,
                   landuse_changed=False):
        z_cost = 0
        l_cost = 0
        # in case of a floodplain lowering, landuse might not change, even
        # though costs for removal (e.g. a building) should be calculated.
        # In such a scenario, landuse_trigger activates the landuse loop.
        landuse_trigger = False
        ownership_change = None
        if z_changed:
            if hexagon_old.properties["z_reference"] >= 5:
                if hexagon_new.properties["z_reference"] >= 4:
                    # dike lowering (for whatever reason)
                    z_type = "lowered reinforced dike [NEEDS costs calculation]"
                else:
                    # relocated reinforced dike from this hexagon
                    z_type = "relocated reinforced dike (removal)"
                    # since dike relocation involves two hexagon changes, costs
                    # are split
                    z_cost = self.hexagon_height * self.dike_m["relocate"] / 2.0
                    ownership_change = "Water"
            elif hexagon_new.properties["z_reference"] >= 5:
                if hexagon_old.properties["z_reference"] >= 4:
                    # dike reinforcement
                    z_type = "reinforced dike"
                    z_cost = self.hexagon_height * self.dike_m["raise"]
                else:
                    # relocated reinforced dike to this hexagon
                    z_type = "relocated reinforced dike (construction)"
                    # since dike relocation involves two hexagon changes, costs
                    # are split
                    z_cost = self.hexagon_height * self.dike_m["relocate"] / 2.0
            elif hexagon_old.properties["z_reference"] >= 4:
                z_type = "dike relocation (removal)"
                ownership_change = "Water"
                # since dike relocation involves two hexagon changes, costs
                # are split
                z_cost = self.hexagon_height * self.dike_m["relocate"] / 2.0
            elif hexagon_new.properties["z_reference"] >= 4:
                z_type = "dike relocation (construction)"
                # since dike relocation involves two hexagon changes, costs
                # are split
                z_cost = self.hexagon_height * self.dike_m["relocate"] / 2.0
            elif hexagon_old.properties["z_reference"] >= 3:
                if hexagon_new.properties["z_reference"] == 2:
                    z_type = "lowered floodplain"
                    z_cost = ((self.hexagon_area *
                               (hexagon_old.properties["z_reference"] -
                                hexagon_new.properties["z_reference"]))
                              * self.floodplain_lowering_m3["storage"])
                    landuse_trigger = True
                else:
                    z_type = "constructed sidechannel"
                    z_cost = ((self.hexagon_area *
                               (hexagon_old.properties["z_reference"] -
                                hexagon_new.properties["z_reference"]))
                              * self.sidechannel_m3["storage"])
                    ownership_change = "Water"
            elif hexagon_new.properties["z_reference"] >= 3:
                if hexagon_old.properties["z_reference"] == 2:
                    z_type = "raised floodplain"
                    z_cost = ((self.hexagon_area *
                               (hexagon_old.properties["z_reference"] -
                                hexagon_new.properties["z_reference"]))
                              * self.floodplain_lowering_m3["storage"])
                else:
                    z_type = "filled up sidechannel (for whatever reason)"
                    z_cost = ((self.hexagon_area *
                               (hexagon_old.properties["z_reference"] -
                                hexagon_new.properties["z_reference"]))
                              * self.sidechannel_m3["storage"])
            elif hexagon_old.properties["z_reference"] >= 2:
                z_type = "constructed sidechannel"
                z_cost = ((self.hexagon_area * (hexagon_old.properties["z_reference"] -
                                                  hexagon_new.properties["z_reference"]))
                          * self.sidechannel_m3["storage"])
                ownership_change = "Water"
            elif hexagon_new.properties["z_reference"] >= 2:
                z_type = "filled up sidechannel (for whatever reason)"
                z_cost = ((self.hexagon_area * (hexagon_old.properties["z_reference"] -
                                                  hexagon_new.properties["z_reference"]))
                          * self.sidechannel_m3["storage"])
            elif hexagon_old.properties["z_reference"] >= 1:
                z_type = "deepened existing sidechannel"
                z_cost = ((self.hexagon_area * (hexagon_old.properties["z_reference"] -
                                                  hexagon_new.properties["z_reference"]))
                          * self.sidechannel_m3["storage"])
            elif hexagon_new.properties["z_reference"] >= 1:
                z_type = "undeepened existing sidechannel"
                z_cost = ((self.hexagon_area * (hexagon_old.properties["z_reference"] -
                                                  hexagon_new.properties["z_reference"]))
                          * self.sidechannel_m3["storage"])
            try:
                z_cost = int(round(abs(z_cost)))
                print("Costs for hexagon " + str(hexagon_new.id) + " for " + z_type + ": " + str(z_cost) + " Euros")
            except UnboundLocalError:
                print("No costs calculated. Perhaps a missing costs scenario"
                      "(elevation change)?")
        if (landuse_changed or landuse_trigger):
            if hexagon_old.properties["landuse"] == 0:
                l_type = "building acquisition and demolition"
                l_cost = self.acqi_type["farm"] + self.demo_type["farm"]
                # This if scenario of when not to assign ownership might need
                # to be changed. Currently doesn't overwrite an ownership
                # change in relation to a dike relocation.
                if (ownership_change is None and
                    hexagon_new.properties["landuse"] != 10):
                    ownership_change = "Province"
            elif hexagon_old.properties["landuse"] == 1:
                l_type = "production grass removal"
                l_cost = self.hexagon_area * self.roughness_smooth_m2["grass"]
            elif hexagon_old.properties["landuse"] == 2:
                l_type = "natural grass removal"
                l_cost = self.hexagon_area * self.roughness_smooth_m2["grass"]
            elif hexagon_old.properties["landuse"] == 3:
                l_type = "herbaceous vegetation removal"
                l_cost = self.hexagon_area * self.roughness_smooth_m2["herbaceous"]
            elif hexagon_old.properties["landuse"] == 4:
                l_type = "forest clearing and removal"
                l_cost = self.hexagon_area * self.roughness_smooth_m2["forest"]
            elif hexagon_old.properties["landuse"] == 5:
                l_type = "forest clearing and removal"
                l_cost = self.hexagon_area * self.roughness_smooth_m2["forest"]
            elif hexagon_old.properties["landuse"] == 6:
                l_type = "vegetation mixtype removal"
            elif hexagon_old.properties["landuse"] == 7:
                l_type = "changing sidechannel to floodplain"
                # no costs in land use changed, all in z changed
                pass
            elif hexagon_old.properties["landuse"] == 8:
                if hexagon_new.properties["landuse"] == 9:
                    l_type = "replacing ltd with groyne"
                    l_cost = self.hexagon_height * self.structures_m["ltd"]
                else:
                    print("INVALID MOVE, no costs calculated")
            elif hexagon_old.properties["landuse"] == 9:
                if hexagon_new.properties["landuse"] == 8:
                    l_type = "replacing groyne with ltd"
                    l_cost = self.hexagon_height * self.structures_m["ltd"]
                else:
                    print("INVALID MOVE, no costs calculated")
            else:
                print("dike relocation")
                # no costs in land use changed, all in z changed
            if hexagon_new.properties["landuse"] == 6:
                ownership_change = "Nature"
            """
            # These could be added to add costs for construction/planting of
            # different land uses.
            
            if hexagon_new.properties["landuse"] == 0:
                print("new building")
                # no costs currently
            elif hexagon_new.properties["landuse"] == 1:
                print("production grass planted")
                # no costs currently
            elif hexagon_new.properties["landuse"] == 2:
                print("natural grass planted")
                # no costs currently
            elif hexagon_new.properties["landuse"] == 3:
                print("herbaceous vegetation planted")
                # no costs currently
            elif hexagon_new.properties["landuse"] == 4:
                print("shrubs planted")
                # no costs currently
            elif hexagon_new.properties["landuse"] == 5:
                print("forest planted")
                # no costs currently
            elif hexagon_new.properties["landuse"] == 6:
                print("mixtype removal")
                # no costs currently
            elif hexagon_new.properties["landuse"] == 7:
                print("changed sidechannel to floodplain")
                # no costs in land use changed, all in z changed
                pass
            elif hexagon_new.properties["landuse"] == 8:
                if hexagon_old.properties["landuse"] == 9:
                    print("replaced groyne with ltd")
                    # no costs in land use changed, already covered above
                else:
                    print("INVALID MOVE, no costs calculated")
            elif hexagon_new.properties["landuse"] == 9:
                if hexagon_old.properties["landuse"] == 8:
                    print("replaced ltd with groyne")
                    # no costs in land use changed, already covered above
                else:
                    print("INVALID MOVE, no costs calculated")
            else:
                print("dike relocation")
                # no costs in land use changed, all in z changed
            """
            try:
                l_cost = int(round(l_cost))
                print("Costs for hexagon " + str(hexagon_new.id) + " for " + l_type + ": " + str(l_cost) + " Euros")
            except UnboundLocalError:
                print("No costs calculated. Perhaps a missing costs scenario"
                      "(landuse change)?")
        if (z_changed and landuse_changed):
            # exceptional situations if they exist?
            pass
        return z_cost, l_cost, ownership_change


    def cost_per_hex(self):
        all_costs = []
        costs = self.getCost(self.acqi_type["farm"], 1, "farm acquisition")
        all_costs.append(costs)
        costs = self.getCost(self.acqi_type["business"], 1, "business acquisition")
        all_costs.append(costs)
        costs = self.getCost(self.demo_type["farm"], 1, "farm demolition")
        all_costs.append(costs)
        costs = self.getCost(self.demo_type["business"], 1, "business demolition")
        all_costs.append(costs)
        costs = self.getCost(self.floodplain_lowering_m3["storage"], self.hexagon_area, "floodplain lowering")
        all_costs.append(costs)
        costs = self.getCost(self.sidechannel_m3["storage"], self.hexagon_area, "digging sidechannel")
        all_costs.append(costs)
        costs = self.getCost(self.roughness_smooth_m2["grass"], self.hexagon_area, "grass smoothing")
        all_costs.append(costs)
        costs = self.getCost(self.roughness_smooth_m2["herbaceous"], self.hexagon_area, "herbaceous smoothing")
        all_costs.append(costs)
        costs = self.getCost(self.roughness_smooth_m2["forest"], self.hexagon_area, "forest smoothing")
        all_costs.append(costs)
        costs = self.getCost(self.structures_m["ltd"], self.hexagon_height, "ltd construction")
        all_costs.append(costs)
        costs = self.getCost(self.dike_m["raise"], self.hexagon_height, "dike reinforcement")
        all_costs.append(costs)
        costs = self.getCost(self.dike_m["relocate"], self.hexagon_height, "dike relocation")
        all_costs.append(costs)
        with open('costs_test.txt', 'w') as f:
            for item in all_costs:
                f.write(item)
                f.write("\n")
        return
            
    def getCost(self, cost_type, multiplier, what):
        calc = cost_type * multiplier
        string = ("Costs for " + str(what) + " per hexagon are: " + str(calc))
        return string


def main():
    """dir_path = os.path.dirname(os.path.realpath(__file__))
    test_path = os.path.join(dir_path, 'test_files')
    turn = 0
    hexagons_old = gridmap.read_hexagons(
            filename='hexagons%d.geojson' % turn,
            path=test_path)
    turn += 1
    hexagons_new = gridmap.read_hexagons(
            filename='hexagons%d.geojson' % turn,
            path=test_path)
    """
    cost = Costs()
    cost.cost_per_hex()


if __name__ == '__main__':
    main()