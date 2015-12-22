def get_ofp_type(of_type):
    of_types = {0: 'Hello',
                1: 'Error',
                2: 'EchoReq',
                3: 'EchoRes',
                4: 'Experimenter',
                5: 'FeatureReq',
                6: 'FeatureRes',
                7: 'GetConfigReq',
                8: 'GetConfigRes',
                9: 'SetConfig',
                10: 'PacketIn',
                11: 'FlowRemoved',
                12: 'PortStatus',
                13: 'PacketOut',
                14: 'FlowMod',
                15: 'GroupMod',
                16: 'PortMod',
                17: 'TableMod',
                18: 'MultipartReq',
                19: 'MiltopartRes',
                20: 'BarrierReq',
                21: 'BarrierRes',
                22: 'QueueGetConfigReq',
                23: 'QueueGetConfigRes',
                24: 'RoleReq',
                25: 'RoleRes',
                26: 'GetAsyncReq',
                27: 'GetAsyncRes',
                28: 'SetAsync',
                29: 'MeterMod'}
    try:
        return of_types[of_type]
    except:
        return 'UnknownType(%s)' % of_type
