using Business.Interfaces;
using Dtos.AosTypeDtos;
using Entities.Concrete;
using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Mvc.Rendering;

namespace UI.ViewComponents {
    public class AosTypeSelectList : ViewComponent {
        private readonly IGenericService _genericService;

        public AosTypeSelectList(IGenericService genericService) {
            _genericService = genericService;
        }

        public async Task<IViewComponentResult> InvokeAsync() {
            var results = await _genericService.GetAll<AosTypeListDto, AosType>();
            var data = new SelectList(results.Data, "Id", "Name", "AosTypeId");
            return View(data);
        }
    }
}