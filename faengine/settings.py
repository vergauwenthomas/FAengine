""" Default settings for the FAengine"""

defaultsettings = {
    'coordnames': {
        #spatial
        'xdim': 'x',
        'ydim': 'y',
        'latcoord': 'lat',
        'loncoord': 'lon',

        #vertical
        'zdim': 'z',

        #temporal
        'validtime': 't',
        'basetime': 't_base'
    }

}

default_units = {
    #SURFEX
    'SFX.T2M': "K",
    'SFX.Q2M': "kg/kg",

    #ALARO/AROME
    'CLSTEMPERATURE': "K",
}

#the blackfields are always skipped
default_blackfields = [
    "SFX.STORAGE_TYPE",
    "SFX.MASDEV",
    "SFX.BUGFIX",
    "SFX.BIBUSER",
    "SFX.PROGRAM",
    "SFX.SURF",
    "SFX.MY_NAME",
    "SFX.DAD_NAME",
    "SFX.L1D",
    "SFX.L2D",
    "SFX.PACK",
    "SFX.VERSION",
    "SFX.BUG",
    "SFX.STORAGETYPE",
    "SFX.DIM_FULL",
    "SFX.WRITE_EXT",
    "SFX.SPLIT_PATCH",
    "SFX.DTCUR",
    "SFX.CARTESIAN",
    "SFX.GRID_TYPE",
    "SFX.LAT0",
    "SFX.LON0",
    "SFX.RPK",
    "SFX.BETA",
    "SFX.LATORI",
    "SFX.LONORI",
    "SFX.IMAX",
    "SFX.JMAX",
    "SFX.SSO_CANOPY",
    "SFX.LCPL_GCM",
    "SFX.BUDC",
    "SFX.SEA_OCEAN",
    "SFX.HANDLE_SIC",
    "SFX.SEA_SBL",
    "SFX.WAT_SBL",
    "SFX.GLACIER",
    "SFX.SN_VEG_TYP",
    "SFX.SN_VEG_N",
    "SFX.SN_VEGP1",
    "SFX.LSNOW_FRAC_T",
    "SFX.SN_VEGP2",
    "SFX.SN_VEGP3",
    "SFX.SOC",
    "SFX.RESPSL",
    "SFX.NLITTER",
    "SFX.NLITTLEVS",
    "SFX.NSOILCARB",
    "SFX.ISBA_CANOPY",
    "SFX.ROAD_DIR",
    "SFX.WALL_OPT",
    "SFX.SN_RF_TYP",
    "SFX.SN_RF_N",
    "SFX.SN_RF",
    "SFX.SN_RD_TYP",
    "SFX.SN_RD_N",
    "SFX.SN_RD",
    "SFX.TEB_CANOPY",
    "SFX._FBUF_SIZE",
    "SFX._FBUF_DIM1",
    "SFX._FBUF_DIM2",
    "SFX._FBUF_NAME",
    "SFX._FBUF_TYPE",
    "SFX._FBUF_MASK",
    "SFX.XX", #is a trivial H2D field
    "SFX.YY",#is a trivial H2D field
    "SFX.DX",#is a trivial H2D field
    "SFX.DY",#is a trivial H2D field
    ]
