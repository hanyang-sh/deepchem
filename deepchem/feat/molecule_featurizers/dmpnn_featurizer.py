# flake8: noqa

import numpy as np
from typing import List, Tuple, Union, Dict, Set, Sequence
import deepchem as dc
from deepchem.utils.typing import RDKitAtom, RDKitMol, RDKitBond

from deepchem.utils.molecule_feature_utils import one_hot_encode
from deepchem.utils.molecule_feature_utils import get_atom_total_degree_one_hot
from deepchem.utils.molecule_feature_utils import get_atom_formal_charge_one_hot
from deepchem.utils.molecule_feature_utils import get_atom_total_num_Hs_one_hot
from deepchem.utils.molecule_feature_utils import get_atom_hybridization_one_hot
from deepchem.utils.molecule_feature_utils import get_atom_is_in_aromatic_one_hot

from deepchem.feat.graph_features import bond_features as b_Feats


class GraphConvConstants(object):
  """
  A class for holding featurization parameters.
  """

  MAX_ATOMIC_NUM = 100
  ATOM_FEATURES: Dict[str, List[int]] = {
      'atomic_num': list(range(MAX_ATOMIC_NUM)),
      'degree': [0, 1, 2, 3, 4, 5],
      'formal_charge': [-1, -2, 1, 2, 0],
      'chiral_tag': [0, 1, 2, 3],
      'num_Hs': [0, 1, 2, 3, 4]
  }
  ATOM_FEATURES_HYBRIDIZATION: List[str] = ["SP", "SP2", "SP3", "SP3D", "SP3D2"]
  # Dimension of atom feature vector
  ATOM_FDIM = sum(len(choices) + 1 for choices in ATOM_FEATURES.values()) + len(
      ATOM_FEATURES_HYBRIDIZATION) + 1 + 2
  # len(choices) +1 and len(ATOM_FEATURES_HYBRIDIZATION) +1 to include room for unknown set
  # + 2 at end for is_in_aromatic and mass
  BOND_FDIM = 14


def get_atomic_num_one_hot(atom: RDKitAtom,
                           allowable_set: List[int],
                           include_unknown_set: bool = True) -> List[float]:
  """Get a one-hot feature about atomic number of the given atom.

  Parameters
  ---------
  atom: RDKitAtom
    RDKit atom object
  allowable_set: List[int]
    The range of atomic numbers to consider.
  include_unknown_set: bool, default False
    If true, the index of all types not in `allowable_set` is `len(allowable_set)`.

  Returns
  -------
  List[float]
    A one-hot vector of atomic number of the given atom.
    If `include_unknown_set` is False, the length is `len(allowable_set)`.
    If `include_unknown_set` is True, the length is `len(allowable_set) + 1`.
  """
  return one_hot_encode(atom.GetAtomicNum() - 1, allowable_set,
                        include_unknown_set)


def get_atom_chiral_tag_one_hot(
    atom: RDKitAtom,
    allowable_set: List[int],
    include_unknown_set: bool = True) -> List[float]:
  """Get a one-hot feature about chirality of the given atom.

  Parameters
  ---------
  atom: RDKitAtom
    RDKit atom object
  allowable_set: List[int]
    The list of chirality tags to consider.
  include_unknown_set: bool, default False
    If true, the index of all types not in `allowable_set` is `len(allowable_set)`.

  Returns
  -------
  List[float]
    A one-hot vector of chirality of the given atom.
    If `include_unknown_set` is False, the length is `len(allowable_set)`.
    If `include_unknown_set` is True, the length is `len(allowable_set) + 1`.
  """
  return one_hot_encode(atom.GetChiralTag(), allowable_set, include_unknown_set)


def get_atom_mass(atom: RDKitAtom) -> List[float]:
  """Get vector feature containing downscaled mass of the given atom.

  Parameters
  ---------
  atom: RDKitAtom
    RDKit atom object

  Returns
  -------
  List[float]
    A vector of downscaled mass of the given atom.
  """
  return [atom.GetMass() * 0.01]


def atom_features(
    atom: RDKitAtom,
    functional_groups: List[int] = None,
    only_atom_num: bool = False) -> Sequence[Union[bool, int, float]]:
  """Helper method used to compute atom feature vector.

  Deepchem already contains an atom_features function, however we are defining a new one here due to the need to handle features specific to DMPNN.

  Parameters
  ----------
  atom: RDKitAtom
    Atom to compute features on.
  functional_groups: List[int]
    A k-hot vector indicating the functional groups the atom belongs to.
    Default value is None
  only_atom_num: bool
    Toggle to build a feature vector for an atom containing only the atom number information.

  Returns
  -------
  features: Sequence[Union[bool, int, float]]
    A list of atom features.

  Examples
  --------
  >>> from rdkit import Chem
  >>> mol = Chem.MolFromSmiles('C')
  >>> atom = mol.GetAtoms()[0]
  >>> features = dc.feat.molecule_featurizers.dmpnn_featurizer.atom_features(atom)
  >>> type(features)
  <class 'list'>
  >>> len(features)
  133
  """

  if atom is None:
    features: Sequence[Union[bool, int,
                             float]] = [0] * GraphConvConstants.ATOM_FDIM

  elif only_atom_num:
    features = []
    features += get_atomic_num_one_hot(
        atom, GraphConvConstants.ATOM_FEATURES['atomic_num'])
    features += [0] * (
        GraphConvConstants.ATOM_FDIM - GraphConvConstants.MAX_ATOMIC_NUM - 1
    )  # set other features to zero

  else:
    features = []
    features += get_atomic_num_one_hot(
        atom, GraphConvConstants.ATOM_FEATURES['atomic_num'])
    features += get_atom_total_degree_one_hot(
        atom, GraphConvConstants.ATOM_FEATURES['degree'])
    features += get_atom_formal_charge_one_hot(
        atom, GraphConvConstants.ATOM_FEATURES['formal_charge'])
    features += get_atom_chiral_tag_one_hot(
        atom, GraphConvConstants.ATOM_FEATURES['chiral_tag'])
    features += get_atom_total_num_Hs_one_hot(
        atom, GraphConvConstants.ATOM_FEATURES['num_Hs'])
    features += get_atom_hybridization_one_hot(
        atom, GraphConvConstants.ATOM_FEATURES_HYBRIDIZATION, True)
    features += get_atom_is_in_aromatic_one_hot(atom)
    features = [int(feature) for feature in features]
    features += get_atom_mass(atom)

    if functional_groups is not None:
      features += functional_groups
  return features


def bond_features(bond: RDKitBond) -> Sequence[Union[bool, int, float]]:
  """wrapper function for bond_features() already available in deepchem, used to compute bond feature vector.

  Parameters
  ----------
  bond: RDKitBond
    Bond to compute features on.

  Returns
  -------
  features: Sequence[Union[bool, int, float]]
    A list of bond features.

  Examples
  --------
  >>> from rdkit import Chem
  >>> mol = Chem.MolFromSmiles('CC')
  >>> bond = mol.GetBondWithIdx(0)
  >>> b_features = dc.feat.molecule_featurizers.dmpnn_featurizer.bond_features(bond)
  >>> type(b_features)
  <class 'list'>
  >>> len(b_features)
  14
  """
  if bond is None:
    b_features: Sequence[Union[
        bool, int, float]] = [1] + [0] * (GraphConvConstants.BOND_FDIM - 1)

  else:
    b_features = [0] + b_Feats(bond, use_extended_chirality=True)
  return b_features


def map_reac_to_prod(
    mol_reac: RDKitMol,
    mol_prod: RDKitMol) -> Tuple[Dict[int, int], List[int], List[int]]:
  """
  Function to build a dictionary of mapping atom indices in the reactants to the products.

  Parameters
  ----------
  mol_reac: RDKitMol
  An RDKit molecule of the reactants.

  mol_prod: RDKitMol
  An RDKit molecule of the products.

  Returns
  -------
  mappings: Tuple[Dict[int,int],List[int],List[int]]
  A tuple containing a dictionary of corresponding reactant and product atom indices,
  list of atom ids of product not part of the mapping and
  list of atom ids of reactant not part of the mapping
  """
  only_prod_ids: List[int] = []
  prod_map_to_id: Dict[int, int] = {}
  mapnos_reac: Set[int] = set(
      [atom.GetAtomMapNum() for atom in mol_reac.GetAtoms()])
  for atom in mol_prod.GetAtoms():
    mapno = atom.GetAtomMapNum()
    if (mapno > 0):
      prod_map_to_id[mapno] = atom.GetIdx()
      if (mapno not in mapnos_reac):
        only_prod_ids.append(atom.GetIdx())
    else:
      only_prod_ids.append(atom.GetIdx())
  only_reac_ids: List[int] = []
  reac_id_to_prod_id: Dict[int, int] = {}
  for atom in mol_reac.GetAtoms():
    mapno = atom.GetAtomMapNum()
    if (mapno > 0):
      try:
        reac_id_to_prod_id[atom.GetIdx()] = prod_map_to_id[mapno]
      except KeyError:
        only_reac_ids.append(atom.GetIdx())
    else:
      only_reac_ids.append(atom.GetIdx())
  mappings: Tuple[Dict[int, int], List[int],
                  List[int]] = (reac_id_to_prod_id, only_prod_ids,
                                only_reac_ids)
  return mappings


class _MapperDMPNN:
  """
  This class is a helper class for DMPNN featurizer to generate concatenated feature vector and mapping.

  `self.f_ini_atoms_bonds_zero_padded` is the concatenated feature vector which contains
  concatenation of initial atom and bond features.

  `self.mapping` is the mapping which maps bond index to 'array of indices of the bonds'
  incoming at the initial atom of the bond (excluding the reverse bonds)
  """

  def __init__(self, datapoint: RDKitMol, concat_fdim: int,
               f_atoms_zero_padded: np.ndarray):
    """
    Parameters
    ----------
    datapoint: RDKitMol
      RDKit mol object.
    concat_fdim: int
      dimension of feature vector with concatenated atom (initial) and bond features
    f_atoms_zero_padded: np.ndarray
      mapping from atom index to atom features | initial input is a zero padding
    """
    self.datapoint = datapoint
    self.concat_fdim = concat_fdim
    self.f_atoms_zero_padded = f_atoms_zero_padded

    # number of atoms
    self.num_atoms: int = len(f_atoms_zero_padded) - 1

    # number of bonds
    self.num_bonds: int = 0

    # mapping from bond index to concat(in_atom, bond) features | initial input is a zero padding
    self.f_ini_atoms_bonds_zero_padded: np.ndarray = np.asarray(
        [[0] * (self.concat_fdim)], dtype=float)

    # mapping from atom index to list of indicies of incoming bonds
    self.atom_to_incoming_bonds: List[List[int]] = [
        [] for i in range(self.num_atoms + 1)
    ]

    # mapping from bond index to the index of the atom the bond is coming from
    self.bond_to_ini_atom: List[int] = [0]

    # mapping from bond index to the index of the reverse bond
    self.b2revb: List[int] = [0]

    self.mapping: np.ndarray = np.empty(0)

    self._generate_mapping()

  def _generate_mapping(self):
    """
    Generate mapping which maps bond index to 'array of indices of the bonds'
    incoming at the initial atom of the bond (reverse bonds are not considered).

    Steps:
    - Iterate such that all bonds in the mol are considered.
      For each iteration: (if bond exists)
      - Update the `self.f_ini_atoms_bonds_zero_padded` concatenated feature vector.
      - Update secondary mappings.
    - Modify `self.atom_to_incoming_bonds` based on maximum number of bonds.
    - Get mapping based on `self.atom_to_incoming_bonds` and `self.bond_to_ini_atom`.
    - Replace reverse bond values with 0
    """
    for a1 in range(1, self.num_atoms + 1):
      for a2 in range(a1 + 1, self.num_atoms + 1):
        if not self._update_concat_vector(a1, a2):
          continue
        self._update_secondary_mappings(a1, a2)
        self.num_bonds += 2
    self._modify_based_on_max_bonds()

    # get mapping which maps bond index to 'array of indices of the bonds' incoming at the initial atom of the bond
    self.mapping = np.asarray(
        self.atom_to_incoming_bonds)[self.bond_to_ini_atom]

    self._replace_rev_bonds()

  def _extend_concat_feature(self, a1: int, bond_feature: np.ndarray):
    """
    Helper method to concatenate initial atom and bond features and append them to `self.f_ini_atoms_bonds_zero_padded`.

    Parameters
    ----------
    a1: int
      index of the atom where the bond starts
    bond_feature: np.ndarray
      array of bond features
    """
    concat_input: np.ndarray = np.concatenate(
        (self.f_atoms_zero_padded[a1], bond_feature),
        axis=0).reshape([1, self.concat_fdim])
    self.f_ini_atoms_bonds_zero_padded = np.concatenate(
        (self.f_ini_atoms_bonds_zero_padded, concat_input), axis=0)

  def _update_concat_vector(self, a1: int, a2: int):
    """
    Method to update `self.f_ini_atoms_bonds_zero_padded` with features of the bond between atoms `a1` and `a2`.

    Parameters
    ----------
    a1: int
      index of the atom 1
    a2: int
      index of the atom 2
    """
    bond: RDKitBond = self.datapoint.GetBondBetweenAtoms(a1 - 1, a2 - 1)
    if bond is None:
      return 0

    # get bond features
    f_bond: np.ndarray = np.asarray(bond_features(bond), dtype=float)

    self._extend_concat_feature(a1, f_bond)
    self._extend_concat_feature(a2, f_bond)
    return 1

  def _update_secondary_mappings(self, a1, a2):
    """
    Method to update `self.atom_to_incoming_bonds`, `self.bond_to_ini_atom` and `self.b2revb`
    with respect to the bond between atoms `a1` and `a2`.

    Parameters
    ----------
    a1: int
      index of the atom 1
    a2: int
      index of the atom 2
    """
    b1: int = self.num_bonds + 1  # bond index
    b2: int = self.num_bonds + 2  # reverse bond index

    self.atom_to_incoming_bonds[a2].append(b1)  # b1 = a1 --> 'a2'
    self.atom_to_incoming_bonds[a1].append(b2)  # b2 = a2 --> 'a1'

    self.bond_to_ini_atom.append(a1)  # b1 starts at a1
    self.bond_to_ini_atom.append(a2)  # b2 starts at a2 (remember, b2 =  b1+1)

    self.b2revb.append(b2)  # reverse bond of b1 is b2
    self.b2revb.append(b1)  # reverse bond of b2 is b1

  def _modify_based_on_max_bonds(self):
    """
    Method to make number of incoming bonds equal to maximum number of bonds.
    This is done by appending zeros to fill remaining space at each atom indicies.
    """
    max_num_bonds: int = max(
        1,
        max(
            len(incoming_bonds)
            for incoming_bonds in self.atom_to_incoming_bonds))
    self.atom_to_incoming_bonds = [
        self.atom_to_incoming_bonds[a] + [0] *
        (max_num_bonds - len(self.atom_to_incoming_bonds[a]))
        for a in range(self.num_atoms + 1)
    ]

  def _replace_rev_bonds(self):
    """
    Method to replace the reverse bond indicies with zeros.
    """
    for count, i in enumerate(self.b2revb):
      self.mapping[count][np.where(self.mapping[count] == i)] = 0
