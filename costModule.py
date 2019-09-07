# -*- coding: utf-8 -*-
"""
Created on Wed Jun 26 14:20:02 2019

@author: HaanRJ
"""


from numpy import sqrt

class Costs():  
    def __init__(self):
        super(Costs, self).__init__()
        self.acqi = None
        self.demo = None
        self.floodplain_lowering = None
        self.sidechannel = None
        self.minor_embankment_m3 = None
        self.roughness_smooth = None
        self.structures = None
        self.dike = None
        self.total_costs = None
        self.hexagon_height = None
        self.hexagon_area = None
        self.total_costs = 0
        self.set_variables()

    def set_variables(self):
        self.acquisition = {
                "agriculture": 362500,
                "nature": 65000,
                "water": 42500,
                "farm": 900000,
                "business": 1400000
                }
        self.demolition = {
                "house": 20000,
                "farm": 40000,
                "business": 120000
                }
        self.floodplain_lowering = {
                "storage": 387500,
                "polluted": 550000,
                "local_use": 162500
                }
        self.sidechannel = {
                "storage": 437500,
                "polluted": 550000,
                "local_use": 162500
                }
        self.minor_embankment_m3 = {
                "storage": 6.9,
                "polluted": 10.2,
                "local_use": 3.1
                }
        self.roughness_smooth = {
                "grass": 3000,
                "herbaceous": 4400,
                "forest": 7200
                }
        self.structures = {
                "lower": 162500,
                "ltd": 475000
                }
        self.dike = {
                "raise": 887500,
                "relocate": 1100000
                }
        
    def set_variables2(self):
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

    def calc_Costs(self, hexagon_new, hexagon_old, mixtype_ratio=[50,20,30],
                   z_changed=False, landuse_changed=False):
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
                    z_cost = self.dike["relocate"] / 2.0
                    if hexagon_old.properties["owner"] != "Water":
                        ownership_change = "Water"
                        if hexagon_old.properties["landuse"] == 0:
                            if hexagon_old.properties["factory"]:
                                z_type = (z_type +
                                          " and factory acquisition and demolition")
                                z_cost = (z_cost + self.acquisition["business"] +
                                          self.demolition["business"])
                            else:
                                z_type = (z_type +
                                          " and farm acquisition and demolition")
                                l_cost = (z_cost + self.acquisition["farm"] +
                                          self.demolition["farm"])
                        elif hexagon_old.properties["landuse"] == 1:
                            z_type = z_type + " and acquired the land"
                            z_cost = (z_cost + self.acquisition["agriculture"])
                        elif (hexagon_old.properties["landuse"] > 1 and
                              hexagon_old.properties["landuse"] < 7):
                            z_type = z_type + " and acquired the land"
                            z_cost = (z_cost + self.acquisition["nature"])
                        else:
                            z_type = z_type + " and acquired the land"
                            z_cost = (z_cost + self.acquisition["water"])
            elif hexagon_new.properties["z_reference"] >= 5:
                if hexagon_old.properties["z_reference"] >= 4:
                    # dike reinforcement
                    z_type = "reinforced dike"
                    z_cost = self.dike["raise"]
                else:
                    # relocated reinforced dike to this hexagon
                    z_type = "relocated reinforced dike (construction)"
                    # since dike relocation involves two hexagon changes, costs
                    # are split
                    z_cost = self.dike["relocate"] / 2.0
            elif hexagon_old.properties["z_reference"] >= 4:
                z_type = "dike relocation (removal)"
                # since dike relocation involves two hexagon changes, costs
                # are split
                z_cost = self.dike["relocate"] / 2.0
                if hexagon_old.properties["owner"] != "Water":
                    ownership_change = "Water"
                    if hexagon_old.properties["landuse"] == 0:
                        if hexagon_old.properties["factory"]:
                            z_type = (z_type +
                                      " and factory acquisition and demolition")
                            z_cost = (z_cost + self.acquisition["business"] +
                                      self.demolition["business"])
                        else:
                            z_type = (z_type +
                                      " and farm acquisition and demolition")
                            l_cost = (z_cost + self.acquisition["farm"] +
                                      self.demolition["farm"])
                    elif hexagon_old.properties["landuse"] == 1:
                        z_type = z_type + " and acquired the land"
                        z_cost = (z_cost + self.acquisition["agriculture"])
                    elif (hexagon_old.properties["landuse"] > 1 and
                          hexagon_old.properties["landuse"] < 7):
                        z_type = z_type + " and acquired the land"
                        z_cost = (z_cost + self.acquisition["nature"])
                    else:
                        z_type = z_type + " and acquired the land"
                        z_cost = (z_cost + self.acquisition["water"])
            elif hexagon_new.properties["z_reference"] >= 4:
                z_type = "dike relocation (construction)"
                # since dike relocation involves two hexagon changes, costs
                # are split
                z_cost = self.dike["relocate"] / 2.0
            elif hexagon_old.properties["z_reference"] >= 3:
                if hexagon_new.properties["z_reference"] == 2:
                    z_type = "lowered floodplain"
                    z_cost = ((hexagon_old.properties["z_reference"] -
                               hexagon_new.properties["z_reference"])
                              * self.floodplain_lowering["storage"])
                    landuse_trigger = True
                else:
                    z_type = "constructed sidechannel"
                    z_cost = ((hexagon_old.properties["z_reference"] -
                                hexagon_new.properties["z_reference"])
                              * self.sidechannel["storage"])
                    if hexagon_old.properties["owner"] != "Water":
                        ownership_change = "Water"
                        if hexagon_old.properties["landuse"] == 0:
                            if hexagon_old.properties["factory"]:
                                z_type = (z_type +
                                          " and factory acquisition and demolition")
                                z_cost = (z_cost + self.acquisition["business"] +
                                          self.demolition["business"])
                            else:
                                z_type = (z_type +
                                          " and farm acquisition and demolition")
                                z_cost = (z_cost + self.acquisition["farm"] +
                                          self.demolition["farm"])
                        elif hexagon_old.properties["landuse"] == 1:
                            z_type = z_type + " and acquired the land"
                            z_cost = (z_cost + self.acquisition["agriculture"])
                        elif (hexagon_old.properties["landuse"] > 1 and
                              hexagon_old.properties["landuse"] < 7):
                            z_type = z_type + " and acquired the land"
                            z_cost = (z_cost + self.acquisition["nature"])
                        else:
                            z_type = z_type + " and acquired the land"
                            z_cost = (z_cost + self.acquisition["water"])
            elif hexagon_new.properties["z_reference"] >= 3:
                if hexagon_old.properties["z_reference"] == 2:
                    z_type = "raised floodplain"
                    z_cost = ((hexagon_old.properties["z_reference"] -
                                hexagon_new.properties["z_reference"])
                              * self.floodplain_lowering["storage"])
                else:
                    z_type = "filled up sidechannel (for whatever reason)"
                    z_cost = ((hexagon_old.properties["z_reference"] -
                                hexagon_new.properties["z_reference"])
                              * self.sidechannel["storage"])
            elif hexagon_old.properties["z_reference"] >= 2:
                z_type = "constructed sidechannel"
                z_cost = ((hexagon_old.properties["z_reference"] -
                            hexagon_new.properties["z_reference"])
                          * self.sidechannel["storage"])
                if hexagon_old.properties["owner"] != "Water":
                    ownership_change = "Water"
                    if hexagon_old.properties["landuse"] == 0:
                        if hexagon_old.properties["factory"]:
                            z_type = (z_type +
                                      " and factory acquisition and demolition")
                            z_cost = (z_cost + self.acquisition["business"] +
                                      self.demolition["business"])
                        else:
                            z_type = (z_type +
                                      " and farm acquisition and demolition")
                            l_cost = (z_cost + self.acquisition["farm"] +
                                      self.demolition["farm"])
                    elif hexagon_old.properties["landuse"] == 1:
                        z_type = z_type + " and acquired the land"
                        z_cost = (z_cost + self.acquisition["agriculture"])
                    elif (hexagon_old.properties["landuse"] > 1 and
                          hexagon_old.properties["landuse"] < 7):
                        z_type = z_type + " and acquired the land"
                        z_cost = (z_cost + self.acquisition["nature"])
                    else:
                        z_type = z_type + " and acquired the land"
                        z_cost = (z_cost + self.acquisition["water"])
            elif hexagon_new.properties["z_reference"] >= 2:
                z_type = "filled up sidechannel (for whatever reason)"
                z_cost = ((hexagon_old.properties["z_reference"] -
                            hexagon_new.properties["z_reference"])
                          * self.sidechannel["storage"])
            elif hexagon_old.properties["z_reference"] >= 1:
                z_type = "deepened existing sidechannel"
                z_cost = ((hexagon_old.properties["z_reference"] -
                            hexagon_new.properties["z_reference"])
                          * self.sidechannel["storage"])
            elif hexagon_new.properties["z_reference"] >= 1:
                z_type = "undeepened existing sidechannel"
                z_cost = ((hexagon_old.properties["z_reference"] -
                            hexagon_new.properties["z_reference"])
                          * self.sidechannel["storage"])
            try:
                z_cost = int(round(abs(z_cost)))
                print("Costs for hexagon " + str(hexagon_new.id) + " for " +
                      z_type + ": " + str(z_cost) + " Euros")
            except UnboundLocalError:
                print("No costs calculated. Perhaps a missing costs scenario"
                      "(elevation change)?")
        if (landuse_changed or landuse_trigger):
            if hexagon_old.properties["landuse"] == 0:
                if (hexagon_old.properties["owner"] is None and
                    ownership_change is None):
                    if hexagon_old.properties["factory"]:
                        l_type = "factory acquisition and demolition"
                        l_cost = (self.acquisition["business"] +
                                  self.demolition["business"])
                    else:
                        l_type = "farm acquisition and demolition"
                        l_cost = (self.acquisition["farm"] +
                                  self.demolition["farm"])
                    # This if scenario of when not to assign ownership might
                    # need to be changed. Currently doesn't overwrite an
                    # ownership change in relation to a dike relocation.
                    if (ownership_change is None and
                        hexagon_new.properties["landuse"] != 10):
                        ownership_change = "Province"
            elif hexagon_old.properties["landuse"] == 1:
                l_type = "production grass removal"
                l_cost = (l_cost + self.roughness_smooth["grass"])
                if (hexagon_old.properties["owner"] is None and
                    ownership_change is None):
                    l_type = l_type + " and agricultural land acquisition"
                    l_cost = l_cost + self.acquisition["agriculture"]
                    # This if scenario of when not to assign ownership might
                    # need to be changed. Currently doesn't overwrite an
                    # ownership change in relation to a dike relocation.
                    if (ownership_change is None and
                        hexagon_new.properties["landuse"] != 10):
                        ownership_change = "Province"
            elif hexagon_old.properties["landuse"] == 2:
                l_type = "natural grass removal"
                l_cost = (l_cost + self.roughness_smooth["grass"])
            elif hexagon_old.properties["landuse"] == 3:
                l_type = "herbaceous vegetation removal"
                l_cost = (l_cost + self.roughness_smooth["herbaceous"])
            elif hexagon_old.properties["landuse"] == 4:
                l_type = "forest clearing and removal"
                l_cost = (l_cost + self.roughness_smooth["forest"])
            elif hexagon_old.properties["landuse"] == 5:
                l_type = "forest clearing and removal"
                l_cost = (l_cost + self.roughness_smooth["forest"])
            elif hexagon_old.properties["landuse"] == 6:
                l_type = "vegetation mixtype removal"
                l_cost = (l_cost + round(
                        ((mixtype_ratio[0] * self.roughness_smooth["grass"] +
                          mixtype_ratio[1] * self.roughness_smooth["herbaceous"] +
                          mixtype_ratio[2] * self.roughness_smooth["forest"]) /
                        10000)) * 100)
            elif hexagon_old.properties["landuse"] == 7:
                l_type = "changing sidechannel to floodplain"
                # no costs in land use changed, all in z changed
                pass
            elif hexagon_old.properties["landuse"] == 8:
                if hexagon_new.properties["landuse"] == 9:
                    l_type = "replacing ltd with groyne"
                    l_cost = self.structures["ltd"]
                else:
                    print("INVALID MOVE, no costs calculated")
            elif hexagon_old.properties["landuse"] == 9:
                if hexagon_new.properties["landuse"] == 8:
                    l_type = "replacing groyne with ltd"
                    l_cost = self.structures["ltd"]
                else:
                    print("INVALID MOVE, no costs calculated")
            else:
                print("dike relocation")
                # no costs in land use changed, all in z changed
            if hexagon_new.properties["landuse"] == 6:
                if hexagon_old.properties["owner"] is None:
                    l_type = l_type + " and acquistion of land"
                    if hexagon_old.properties["landuse"] == 1:
                        l_cost = (l_cost + self.acquisition["agriculture"])
                    elif (hexagon_old.properties["landuse"] > 1 and
                          hexagon_old.properties["landuse"] < 7):
                        l_cost = (l_cost + self.acquisition["nature"])
                    else:
                        l_cost = (l_cost + self.acquisition["water"])
                # Changing to a nature area overwrites ownership. The if
                # exception should never happen, but is there to cover just in
                # case.
                if ownership_change != "Water":
                    ownership_change = "Nature"
                #    if ownership_change is None:
                #        ownership_change = "Nature"
            elif hexagon_new.properties["landuse"] == 7:
                # this elif statement is for redundancy in this specific case.
                ownership_change = "Water"
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
                print("Costs for hexagon " + str(hexagon_new.id) + " for " +
                      l_type + ": " + str(l_cost) + " Euros")
            except UnboundLocalError:
                print("No costs calculated. Perhaps a missing costs scenario"
                      "(landuse change)?")
        if (z_changed and landuse_changed):
            # exceptional situations if they exist?
            pass
        return z_cost, l_cost, ownership_change


    def cost_per_hex(self):
        all_costs = []
        costs = self.get_cost(self.acquisition["agriculture"],
                              self.hexagon_area, "agricultural land acquisition")
        all_costs.append(costs)
        costs = self.get_cost(self.acquisition["nature"], self.hexagon_area,
                              "non-production land acquisition")
        all_costs.append(costs)
        costs = self.get_cost(self.acquisition["water"], self.hexagon_area,
                              "water acquisition")
        all_costs.append(costs)
        costs = self.get_cost(self.acquisition["farm"], 1, "farm acquisition")
        all_costs.append(costs)
        costs = self.get_cost(self.acquisition["business"], 1,
                              "business acquisition")
        all_costs.append(costs)
        costs = self.get_cost(self.demolition["farm"], 1, "farm demolition")
        all_costs.append(costs)
        costs = self.get_cost(self.demolition["business"], 1,
                              "business demolition")
        all_costs.append(costs)
        costs = self.get_cost(self.floodplain_lowering["storage"],
                              self.hexagon_area, "floodplain lowering")
        all_costs.append(costs)
        costs = self.get_cost(self.sidechannel["storage"], self.hexagon_area,
                              "digging sidechannel")
        all_costs.append(costs)
        costs = self.get_cost(self.roughness_smooth["grass"],
                              self.hexagon_area, "grass smoothing")
        all_costs.append(costs)
        costs = self.get_cost(self.roughness_smooth["herbaceous"],
                              self.hexagon_area, "herbaceous smoothing")
        all_costs.append(costs)
        costs = self.get_cost(self.roughness_smooth["forest"],
                              self.hexagon_area, "forest smoothing")
        all_costs.append(costs)
        costs = self.get_cost(self.structures["ltd"], self.hexagon_height,
                              "ltd construction")
        all_costs.append(costs)
        costs = self.get_cost(self.dike["raise"], self.hexagon_height,
                              "dike reinforcement")
        all_costs.append(costs)
        costs = self.get_cost(self.dike["relocate"], self.hexagon_height,
                              "dike relocation")
        all_costs.append(costs)
        with open('costs_test.txt', 'w') as f:
            for item in all_costs:
                f.write(item)
                f.write("\n")
        return
            
    
    def update_total_costs(self):
        return
    
    
    def get_cost(self, cost_type, multiplier, what):
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