"""Canonicalize explicitly conductive PCB interconnects for schematic export."""
def net_aliases(assembly):
    nets={n for part in assembly['parts'] for n in part['pins'].values() if n and n!='NC'}
    parent={n:n for n in nets}
    def find(n):
        while parent[n]!=n:
            parent[n]=parent[parent[n]];n=parent[n]
        return n
    for link in assembly.get('interconnects',[]):
        if link['type']!='PCB trace, not a resistor':
            raise ValueError('Unsupported interconnect type: '+link['type'])
        left,right=link['from'],link['to']
        if left not in nets or right not in nets:raise ValueError('Unknown trace endpoint')
        x,y=sorted([find(left),find(right)]);parent[y]=x
    return {n:find(n) for n in nets}
