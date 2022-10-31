using Business.Interfaces;
using Dtos.StreamDtos;
using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Mvc.Rendering;

namespace UI.ViewComponents {
    public class StreamSelectList : ViewComponent {

        private readonly IGenericService _genericService;

        public StreamSelectList(IGenericService genericService) {
            _genericService = genericService;
        }

        public async Task<IViewComponentResult> InvokeAsync() {
            var results = await _genericService.GetListByFilter<StreamListDto, Entities.Concrete.Stream>(x => x.IsVideo != true);
            var data = new SelectList(results.Data, "Id", "Name", "StreamId"); //arguments --> (Id="", InnerHtml="", Name="")
            return View(data);
        }

    }
}