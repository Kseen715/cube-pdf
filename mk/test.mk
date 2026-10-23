# The tests of the OCR core (tests/core): test-core links the core's shared
# objects with the tests and runs them against what "core" builds. Only the
# native Linux build can run them.

ifeq ($(TARGET),linux)

TEST_SRC := tests/core
TEST_OBJ := $(T)/obj/test
TEST_CORE := $(T)/test-core
TEST_OBJS := $(patsubst $(TEST_SRC)/%,$(TEST_OBJ)/%.o,$(basename \
    $(wildcard $(TEST_SRC)/*.c $(TEST_SRC)/*.cpp)))

$(TEST_OBJ)/%.o: $(TEST_SRC)/%.c $(LIBS_STAMPS)
	mkdir -p $(@D)
	$(CC) $(CORE_CFLAGS) -I$(CORE_SRC) -c $< -o $@

$(TEST_OBJ)/%.o: $(TEST_SRC)/%.cpp $(LIBS_STAMPS)
	mkdir -p $(@D)
	$(CXX) $(CORE_CXXFLAGS) -I$(CORE_SRC) -c $< -o $@

-include $(wildcard $(TEST_OBJ)/*.d)

$(TEST_CORE): $(call core_objs,$(CORE_COMMON)) $(TEST_OBJS)
	$(CXX) -o $@ $^ $(CORE_LIBS) $(CORE_LDFLAGS)

test: core $(TEST_CORE)
	$(TEST_CORE) $(BIN)

.PHONY: test

endif
