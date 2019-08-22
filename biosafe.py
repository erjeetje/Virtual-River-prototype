# -*- coding: utf-8 -*-

import numpy as np
import pandas as pd
import os
version = '0.2'

def pjoin(in_dir, file_name):
    return os.path.join(in_dir, file_name)

def aggregateEcotopes(linksEco, lookupTable):
    """Add additional ecotope columns to the linkage of species and ecotopes
    based on the lookup table
    """
    #- filter the lookup table for ecotopes already present in the links df
    bsEcotopes = linksEco.columns.values
    lut = lookupTable.copy()
    lut['inBS'] = lut.oldEcotope.isin(bsEcotopes)
    lut = lut[lut.inBS == True]
    
    #-loop over the ecotopes to be added and sum up species-ecotope links
    linksEcoNew = linksEco.copy().iloc[:,0:-1]
    newEcotopes = np.unique(lut.newEcotope.values)
    for newEcotope in newEcotopes:
        oldEcotopes = lut[lut.newEcotope == newEcotope]
        ecoLinksNew = linksEco.loc[:,oldEcotopes.oldEcotope.values]
        linksEcoNew[str(newEcotope)] = ecoLinksNew.sum(axis=1).clip(upper=1)
    linksEcoNew['taxonomicGroup'] = linksEco.taxonomicGroup
    return linksEcoNew 

def output2xlsx(model, filePath):
    """Writes an instance of the biodiversity model to an excel files
    
    model   : biosafe instance
    filePath: excel (xlsx) file on disk
    
    returns
    -------
    excel file on disk with separate sheets for all parameters
    """
    SScoresSpecies = model.SScoresSpecies()
    summarySScores = model.taxGroupSums()
    SEcoPot = model.SEcoPot()
    SEcoAct = model.SEcoAct()
    PTE = model.PTE()
    ATE = model.ATE()
    TES = model.TES()
    TEI = model.TEI()
    ATEI = model.ATEI()
    TFI = model.TFI()         
    FI = model.FI()
    ATFI = model.ATFI()         
    AFI = model.AFI()
    TFIS = model.TFIS()
    FIS = model.FIS()
    TFHS = model.TFHS()
    
    print('Writing excel output to %s' % filePath)
    writer = pd.ExcelWriter(filePath)
    model.weightsLegal.to_excel(writer, 'weightsLegal')
    model.linksLaw.to_excel(writer, 'linksLaw')
    model.linksEco.to_excel(writer, 'linksEco')
    model.speciesPresence.to_excel(writer, 'speciesPresence')
    model.ecotopeArea.to_excel(writer, 'ecotopeArea')
    SScoresSpecies.to_excel(writer, 'SScoresSpecies')
    summarySScores.to_excel(writer, 'summarySScores')
    SEcoPot.to_excel(writer, 'SEcoPot')
    SEcoAct.to_excel(writer, 'SEcoAct')
    PTE.to_excel(writer, 'PTE')
    ATE.to_excel(writer, 'ATE')
    TES.to_excel(writer, 'TES')
    TEI.to_excel(writer, 'TEI')
    ATEI.to_excel(writer, 'ATEI')
    TFI.to_excel(writer, 'TFI')
    FI.to_excel(writer, 'FI')
    ATFI.to_excel(writer, 'ATFI')
    AFI.to_excel(writer, 'AFI')
    TFIS.to_excel(writer, 'TFIS')
    FIS.to_excel(writer, 'FIS')
    TFHS.to_excel(writer, 'TFHS')
    writer.save()

class biosafe(object):
    """Compute BIOSAFE scores based on paper of De Nooij et al. (2004) 
    
    Parameters: 
        linksEco
        linksLaw
        weightsLegal
        speciesPresence
        ecotopeArea
    """
    
    def __init__(self, weightsLegal, linksLaw, linksEco, speciesPresence, ecotopeArea):
        self.linksEco = linksEco
        self.linksLaw = linksLaw
        self.weightsLegal = weightsLegal
        self.speciesPresence = speciesPresence
        self.ecotopeArea = ecotopeArea
    
    def SScoresSpecies(self):
        """
        Compute the species specific S-Scores based on laws and regulations
        both potential and actual scores
        
        Returns
        -------
        A data frame with columns SPotential, SActual, speciesPresence, taxonomicGroup
        """
        
        weightedLinksLegal = self.linksLaw.iloc[:,2:18].mul(self.weightsLegal.weights, axis = 1)
        SScores = pd.DataFrame(weightedLinksLegal.sum(axis=1), columns = ['SPotential'])
        SScores['SActual'] = SScores.SPotential.mul(self.speciesPresence.speciesPresence, axis=0)
        # add two columns for convenience
        df1 = SScores.join(self.speciesPresence) # add species presence for checking
        df2 = df1.join(self.linksLaw.taxonomicGroup)
        return df2
    
    def SEcoPot(self):
        """Computes the species specific S scores for each ecotope separately
        
        Returns
        -------
        SEcoPot:    Potential Species-specific S-scores per ecotope
        """
        
        links = self.linksEco.iloc[:,0:-1]
        SEcoPot = links.mul(self.SScoresSpecies().SPotential, axis=0)
        SEcoPot['taxonomicGroup'] = self.linksLaw.taxonomicGroup
        return SEcoPot

    def SEcoAct(self):
        """Computes the species specific S scores for each ecotope separately
        
        Returns
        -------
        SEcoAct:    Actual Species-specific S-scores per ecotope AS_eco
        """
        
        links = self.linksEco.iloc[:,0:-1]
        SEcoAct = links.mul(self.SScoresSpecies().SActual, axis=0)
        SEcoAct['taxonomicGroup'] = self.linksLaw.taxonomicGroup
        return SEcoAct        
    
    def taxGroupSums(self):
        """Summarizes the total potential and actual biodiversity
        
        Returns
        -------
        PTB:    Potential Taxonomic group Biodiversity constant, 
                based on laws and regulations
        ATB:    Actual Taxonomic group Biodiversity constant, 
                based on species presence
        TBS:    Taxonomic group Biodiversity Saturation,
                which is 100 * ATB / PTB
        """
        sums = self.SScoresSpecies().groupby('taxonomicGroup', as_index = False).sum()
        sums.drop('speciesPresence', inplace=True, axis=1)
        sums.columns = ['taxonomicGroup', 'PTB', 'ATB']
        sums['TBS'] = sums['ATB'] * 100 / sums['PTB']
        sums.set_index('taxonomicGroup', drop=True, inplace=True) 
        return sums
    
    def PTE(self):
        """ PTE: Potential Taxonomic group Ecotope constant 
            Sum of Potential S_eco scores per taxonomic group for each ecotope
                 = sum of SEcoPot
        """
        PTE = self.SEcoPot().groupby('taxonomicGroup').sum()
        return PTE
    
    def ATE(self):
        """ PTE: Potential Taxonomic group Ecotope constant 
            Sum of Potential S_eco scores per taxonomic group for each ecotope
                 = sum of SEcoPot
        """
        ATE = self.SEcoAct().groupby('taxonomicGroup').sum()
        return ATE
    
    def TES(self):
        """ TES: Taxonomic group Ecotope Saturation index
        """
        TES = 100 * self.ATE() / self.PTE()
        return TES.fillna(value = 0)
    
    def TEI(self):
        """ TEI: Taxonomic group Ecotope Importance constant
        """
        TEI = 100 * self.PTE().div(self.taxGroupSums().PTB, axis = 'index')
        return TEI
    
    def ATEI(self):
        """ ATEI: Actual Taxonomic group Ecotope Importance scores
        """
        return 0.01 * self.TEI() * self.TES()
        
    def TFI(self):
        """ TFI: Taxonomic group Floodplain Importance Score
        """
        ecoAreas  = self.ecotopeArea.copy()
        totalArea = ecoAreas.area_m2.sum(axis = 0)
        ecoAreas['fraction'] = ecoAreas.area_m2 / totalArea
        fracTEI = self.TEI() * ecoAreas['fraction']
        TFI = fracTEI.sum(axis = 1)
        return pd.DataFrame(TFI, columns = ['TFI'])

    def FI(self):
        """ FI: Floodplain Importance score
        """
        FI = self.TFI().sum()
        FI = pd.DataFrame(FI, columns = ['FI'])
        FI.index = ['FI']
        return FI
        
    
    def ATFI(self):
        """ ATFI: Actual Taxonomic group Floodplain Importance Score
        """
        ecoAreas  = self.ecotopeArea.copy()
        totalArea = ecoAreas.area_m2.sum(axis = 0)
        ecoAreas['fraction'] = ecoAreas.area_m2 / totalArea
        fracTEI = self.ATEI() * ecoAreas['fraction']
        ATFI = fracTEI.sum(axis = 1)
        return pd.DataFrame(ATFI, columns = ['ATFI'])

    def AFI(self):
        """ FI: Actual Floodplain Importance score
        """
        AFI = self.ATFI().sum()
        AFI = pd.DataFrame(AFI, columns = ['AFI'])
        AFI.index = ['AFI'] 
        return AFI

    def TFIS(self):
        """TFIS: Taxonomic Group Floodplain Importance Saturation
        Describes the fraction of actual over potential biodiversity value"""
        TFIS = 100 * self.ATFI().ATFI.values / self.TFI().TFI.values
        return pd.DataFrame(TFIS, columns = ['TFIS'], index=self.TFI().index.values)
    
    def FIS(self):
        """FIS: Floodplain Importance Saturation
        Describes the fraction of actual over potential biodiversity value per
        taxonomic group."""
        FIS = 100* self.AFI().AFI.values / self.FI().FI.values
        return pd.DataFrame(FIS, columns = ['FIS'], index=['FIS'])
    
    def TFHS(self):
        """TFHS: Taxonomic Group Floodplain Habitat Saturation.
        Describes the fraction of suitable ecotopes, weighted by law.
        Computed as present floodplain TEI for present ecotopes over
        all possible floodplain ecotopes relevant for the taxonomic group.
        """
        #-FTEI: Floodplain TEI, TEI summed over all ecotopes
        FTEI = self.TEI().sum(axis=1) 
        
        #-PFTEI: Floodplain TEI, TEI summed over the whole area 
        # for ecotopes present
        ecoArea = self.ecotopeArea
        ecoPresence = ecoArea.area_m2 > 0
        PFTEI = self.TEI().mul(ecoPresence, axis=1).sum(axis=1)
        
        #-TFHS: Taxonomic Group Floodplain Habitat Suitability
        TFHS = 100 * PFTEI / FTEI
        return pd.DataFrame(TFHS, columns=['TFHS'])
    
    def FTEI(self):
        """ FTEI: Floodplain Taxonomic group Ecotope Importance
        """
        ecoAreas  = self.ecotopeArea.copy()
        totalArea = ecoAreas.area_m2.sum(axis = 0)
        ecoAreas['fraction'] = ecoAreas.area_m2 / totalArea
        FTEI = 100 * self.TEI() * ecoAreas['fraction']
        return FTEI.fillna(0)
        
if __name__ == '__main__':
    # initiate biosafe 
    
    # Directory settings
    root_dir = os.path.dirname(os.getcwd())
    scratch_dir = os.path.join(root_dir, 'scratch')
    input_dir  = os.path.join(root_dir, 'input_data')
    os.chdir(scratch_dir)
    
    # Input data
    legal_weights = pd.read_csv(pjoin(input_dir, 'legalWeights.csv'), index_col = 0)
    links_law = pd.read_csv(pjoin(input_dir, 'linksLaw.csv'), index_col = 0)
    links_eco1 = pd.read_csv(pjoin(input_dir, 'linksEco.csv'), index_col = 0)
    lut = pd.read_excel(pjoin(input_dir, 'BIOSAFE_20190711.xlsx'),
                         sheet_name = 'lut_RWES').fillna(method='ffill')
        # this lookup table (lut) has:
        #       ecotope codes of BIOSAFE in the first column: oldEcotope
        #       aggregated/translated ectotopes in the second column: newEcotope
    
    # Aggregate Biosafe ecotopes into RWES ecotopes
    links_eco2 = aggregateEcotopes(links_eco1, lut)
    
    # Generate dummy data in the right format
    species_presence = pd.DataFrame(np.random.randint(2, size=len(links_law)),
                                    columns=['speciesPresence'],
                                    index=links_law.index)
    
    ecotope_area = pd.DataFrame(np.ones(len(links_eco2.columns)-1) * 1e5,
                                columns = ['area_m2'],
                                index = links_eco2.columns.values[0:-1])
    
    # Run a first version of Biosafe
    bsf = biosafe(legal_weights, links_law, links_eco2,
                  species_presence, ecotope_area)

    SScoresSpecies = bsf.SScoresSpecies()
    summarySScores = bsf.taxGroupSums()
    SEcoPot = bsf.SEcoPot()
    SEcoAct = bsf.SEcoAct()
    PTE = bsf.PTE()
    ATE = bsf.ATE()
    TES = bsf.TES()
    TEI = bsf.TEI()
    ATEI = bsf.ATEI()
    PotTax = bsf.TFI()         
    PotAll = bsf.FI()
    ATFI = bsf.ATFI()         
    AFI = bsf.AFI()
    FIS = bsf.FIS()
    TFIS = bsf.TFIS()
    TFHS = bsf.TFHS()
    FTEI = bsf.FTEI()
    
    output2xlsx(bsf, 'biosafe_output.xlsx')
