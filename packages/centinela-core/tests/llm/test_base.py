"""Tests for UniversalProviderAdapter abstract base class."""

from __future__ import annotations

from centinela.core.llm import UniversalProviderAdapter


class TestUniversalProviderAdapter:
    """ABC enforcement — cannot instantiate directly, abstract methods enforced."""

    def test_cannot_instantiate_abc(self) -> None:
        """Direct instantiation of ABC must raise TypeError."""
        import pytest

        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            UniversalProviderAdapter()  # type: ignore[abstract]

    def test_missing_generate_raises(self) -> None:
        """Subclass without generate() must raise TypeError."""
        import pytest

        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            type("BadAdapter", (UniversalProviderAdapter,), {})()

    def test_missing_generate_stream_raises(self) -> None:
        """Subclass without generate_stream() must raise TypeError."""
        import pytest

        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            type(
                "BadAdapter",
                (UniversalProviderAdapter,),
                {
                    "generate": lambda self, m, **kw: None,
                },
            )()

    def test_missing_count_tokens_raises(self) -> None:
        """Subclass without count_tokens() must raise TypeError."""
        import pytest

        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            type(
                "BadAdapter",
                (UniversalProviderAdapter,),
                {
                    "generate": lambda self, m, **kw: None,
                    "generate_stream": lambda self, m, **kw: None,
                },
            )()

    def test_all_abstract_methods_enforced(self) -> None:
        """Implementing all 3 abstract methods should allow instantiation."""
        adapter = type(
            "GoodAdapter",
            (UniversalProviderAdapter,),
            {
                "_config": None,
                "model": property(lambda self: "test"),
                "provider": property(lambda self: "test"),
                "generate": lambda self, m, **kw: None,
                "generate_stream": lambda self, m, **kw: None,
                "count_tokens": lambda self, m: 0,
            },
        )()
        assert hasattr(adapter, "generate")
        assert hasattr(adapter, "generate_stream")
        assert hasattr(adapter, "count_tokens")
        assert adapter.model == "test"
        assert adapter.provider == "test"

    def test_abstract_method_signatures(self) -> None:
        """Verify the ABC defines correct method signatures (duck-type check)."""
        required = {"generate", "generate_stream", "count_tokens"}
        methods = {name for name in dir(UniversalProviderAdapter) if not name.startswith("_")}
        assert required.issubset(methods), f"Missing abstract methods: {required - methods}"
