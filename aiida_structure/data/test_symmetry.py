def test_basic(new_database):
    from aiida_structure.data.symmetry import SymmetryData
    node = SymmetryData()
    node.set_data({
        "space_group": 1,
        "operations": [
            [1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0]
        ]
    })
    assert node.space_group == 1
    assert node.num_symops == 1
