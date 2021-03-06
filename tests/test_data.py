import pytest
from mock import MagicMock, call
from numpy.testing import assert_array_equal, assert_array_almost_equal
import data
from data import *


class TestCountFiles:
    def test_no_file(self):
        assert 0 == count_files("%d.png", 1000, lambda name: False)

    def test_checks_file(self):
        exist = MagicMock(name='exist')
        exist.return_value = False
        count_files("test%02d.png", 100, exist)
        assert exist.call_args_list == [call("test99.png"), call("test09.png"), call("test00.png")]

    def test_determines_count(self):
        assert 1234 == count_files("%d", 1000, lambda name: int(name) < 1234)



class TestRandomChoice:
    def test_select_one_of_one(self):
        assert_array_equal(random_choice(1, 1), [0])

    def test_select_one_of_ten(self):
        result = random_choice(10, 1)
        assert result[0] >= 0 and result[0] < 10

    def test_select_distinct_values(self):
        assert sorted(random_choice(10, 10)) == list(range(10))


class TestRandomSelection:
    @pytest.fixture
    def choose_first(self, monkeypatch):
        monkeypatch.setattr(data, 'random_choice', lambda count, size: range(size))

    @pytest.fixture
    def choose_last(self, monkeypatch):
        monkeypatch.setattr(data, 'random_choice', lambda count, size: range(count - size, count))

    def test_select_one(self):
        assert_array_equal(random_selection(1, [42]), [42])

    def test_select_first_of_two(self, choose_first):
        assert_array_equal(random_selection(1, [3, 5]), [3])

    def test_select_second_of_two(self, choose_last):
        assert_array_equal(random_selection(1, [3, 5]), [5])

    def test_select_from_multiple_arrays(self, choose_first):
        result = random_selection(1, [1, 2, 3], [4, 5, 6])
        assert_array_equal(result[0], [1])
        assert_array_equal(result[1], [4])

    def test_select_from_2d_array(self):
        assert_array_equal(random_selection(1, [[1, 2, 3]]), [[1, 2, 3]])


class TestDownSample:
    def test_shape(self):
        assert down_sample(np.empty((240, 320)), 10).shape == (24, 32)


class TestToGray:
    def test_shape(self):
        assert to_gray(np.empty((24, 32, 3))).shape == (24, 32)

    def test_content(self):
        assert_array_equal(to_gray([[[24, 32, 40]]]), [[33]])


class TestMultiClassLabel:
    def test_one_class_label(self):
        assert_array_equal(multi_class_label([0], 1), [[1]])

    def test_two_class_label(self):
        assert_array_equal(multi_class_label([1], 2), [[0, 1]])

    def test_first_class_of_two(self):
        assert_array_equal(multi_class_label([0], 2), [[1, 0]])

    def test_two_samples(self):
        assert_array_equal(multi_class_label([1, 0], 3), [[0, 1, 0], [1, 0, 0]])

    def test_return_type(self):
        assert multi_class_label([0], 1).dtype != np.bool


class TestOperation:
    def test_load_and_save(self):
        bias = Bias([2, 3])
        bias.save('/tmp/bias')
        operation = Operation.restore('/tmp/bias')
        assert_array_equal(operation([5, 7]), [7, 10])


class TestFeatureScale:
    def test_trivial(self):
        assert_array_equal(FeatureScale([[0]])([0]), [0])

    def test_remove_average(self):
        assert_array_equal(FeatureScale([[2], [4]])([4]), [1])

    def test_multiple_averages(self):
        assert_array_equal(FeatureScale([[2, 4]])([2, 4]), [0, 0])

    def test_scale_variance(self):
        assert_array_equal(FeatureScale([[1], [5]])([5]), [1])

    def test_limit_scaling(self):
        assert_array_equal(FeatureScale([[1]], None, 100)([3]), [200])

    def test_nest_operations(self):
        assert_array_equal(FeatureScale([[1]], Offset(-2))([1]), [2])


class TestOffset:
    def test_trivial(self):
        assert_array_equal(Offset(0)([2, 3, 5]), [2, 3, 5])

    def test_apply_offset(self):
        assert_array_equal(Offset(-3)([2, 3, 5]), [5, 6, 8])

    def test_nest_operations(self):
        assert_array_equal(Offset(-3, Scale(0.5))([2, 3, 5]), [7, 9, 13])

    def test_no_variables(self):
        assert Offset(0).variables() == []


class TestScale:
    def test_trivial(self):
        assert_array_equal(Scale(1)([2, 3, 5]), [2, 3, 5])

    def test_use_scale_factor(self):
        assert_array_equal(Scale(0.5)([2, 3, 5]), [4, 6, 10])

    def test_nest_operations(self):
        assert_array_equal(Scale(0.5, Offset(-3))([2, 3, 5]), [10, 12, 16])


class TestReshape:
    def test_trivial(self):
        assert_array_equal(Reshape([-1])([2, 3, 5, 7, 11, 13]), [2, 3, 5, 7, 11, 13])

    def test_reshaping(self):
        assert_array_equal(Reshape([-1, 3])([2, 3, 5, 7, 11, 13]), [[2, 3, 5], [7, 11, 13]])

    def test_nest_operations(self):
        assert_array_equal(Reshape([-1, 2], Offset(-1))([2, 3, 5, 7]), [[3, 4], [6, 8]])


class TestSigmoid:
    def test_values(self):
        assert_array_almost_equal(Sigmoid()([-20, 0, 20]), [0, 0.5, 1])

    def test_nest_operations(self):
        assert_array_almost_equal(Sigmoid(Offset(-20))([-20, 0, 20]), [0.5, 1, 1])


class TestReLU:
    def test_values(self):
        assert_array_equal(ReLU()([-5, 0, 5]), [0, 0, 5])

    def test_nest_operations(self):
        assert_array_equal(ReLU(Offset(-1))([-5, 0, 5]), [0, 1, 6])


class TestWeights:
    def test_apply_weights(self):
        assert_array_equal(Weights([[2, 3, 5], [3, 5, 7]])([[2, 3]]), [[13, 21, 31]])

    def test_single_input(self):
        assert_array_equal(Weights([[2, 3, 5], [3, 5, 7]])([2, 3]), [13, 21, 31])

    def test_nest_operations(self):
        assert_array_equal(Weights([[2, 3, 5], [3, 5, 7]], Offset(-1))([2, 3]), [18, 29, 43])

    def test_get_variables(self):
        weights = Weights([[2, 3, 5], [3, 5, 7]])
        assert weights.variables() == [weights.weights]

    def test_variables_of_nested_expression(self):
        weights = Weights([[2, 3], [3, 5]])
        weights2 = Weights([[2, 3], [3, 5]], weights)
        assert weights2.variables() == [weights.weights, weights2.weights]

    def test_get_regularisation_candidates(self):
        weights = Weights([[2, 3, 5], [3, 5, 7]])
        assert weights.regularisation_candidates() == [weights.weights]

    def test_regularisation_candidates_of_nested_expression(self):
        weights = Weights([[2, 3], [3, 5]])
        weights2 = Weights([[2, 3], [3, 5]], weights)
        assert weights2.regularisation_candidates() == [weights.weights, weights2.weights]

    def test_only_weights_are_regularisation_candidates(self):
        bias = Bias([2, 3])
        weights = Weights([[2, 3], [5, 7]], bias)
        assert weights.regularisation_candidates() == [weights.weights]

    def test_shape(self):
        assert Weights([[2, 3, 5], [3, 5, 7]]).shape() == [2, 3]


class TestBias:
    def test_apply_offset(self):
        assert_array_equal(Bias([2, 3])([5, 7]), [7, 10])

    def test_nesting(self):
        assert_array_equal(Bias([2, 3], Offset(-1))([5, 7]), [8, 11])

    def test_batch(self):
        assert_array_equal(Bias([2, 3])([[2, 3], [5, 7]]), [[4, 6], [7, 10]])

    def test_get_variables(self):
        bias = Bias([2, 3])
        assert bias.variables() == [bias.bias]

    def test_get_regularisation_candidates(self):
        assert Bias([2, 3]).regularisation_candidates() == []

    def test_variables_of_nested_expression(self):
        bias = Bias([5, 7])
        bias2 = Bias([2, 3], bias)
        assert bias2.variables() == [bias.bias, bias2.bias]

    def test_regularisation_candidates_of_nested_expression(self):
        weights = Weights([[2, 3], [5, 7]])
        bias = Bias([2, 3], weights)
        assert bias.regularisation_candidates() == [weights.weights]

    def test_shape(self):
        assert Bias([2, 3, 5]).shape() == [3]


class TestSoftmax:
    def test_normalise(self):
        assert_array_almost_equal(Softmax()([2, 3, 5]), [0.042, 0.114, 0.844], decimal=3)

    def test_only_last_dimension(self):
        assert_array_almost_equal(Softmax()([[1, 1, 1], [2, 3, 5]]),
                                            [[0.333, 0.333, 0.333], [0.042, 0.114, 0.844]], decimal=3)

    def test_nesting(self):
        assert_array_almost_equal(Softmax(Bias([4, 3, 1]))([2, 3, 5]), [0.333, 0.333, 0.333], decimal=3)


class TestRegularisation:
    def test_regularise_weights(self):
        assert Regularisation(Weights([[2, 3]]))([[0]]) == 6.5

    def test_ignore_bias(self):
        assert Regularisation(Bias([5, 7], Weights([[2, 3]])))([[0]]) == 6.5

    def test_regularise_all_weights(self):
        assert Regularisation(Weights([[2]], Weights([[3]])))([[0]]) == 6.5

    def test_divide_by_mini_batch_size(self):
        assert Regularisation(Weights([[2]], Weights([[3]])))([[0], [0]]) == 3.25
